from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count:
        raise SystemExit(f"{label}: expected {count}, got {n}")
    s=s.replace(old,new,count)

rep("// @version      1.18.87",
    "// @version      1.18.88\n// @release-note Карта сокровищ: введены жёсткие транзакционные барьеры. Старая модалка всегда закрывается до новой клетки; бой прокручивает к врагу и к кнопке атаки даже ниже экрана; сундуки не переходят к следующему lot без подтверждения изменения/награды; найденный ключ блокирует любой модуль до завершения.",
    "version")
rep("const BUILD_VERSION = '1.18.87';",
    "const BUILD_VERSION = '1.18.88';",
    "build")

rev_anchor="  const HK_BATTLE_ACTION_MODAL_DIV_REV='battle-action-modal-div-20260929-r1';"
rep(rev_anchor,
    rev_anchor+"\n  const HK_TREASURE_TXN_GATE_REV='treasure-transaction-gate-20260929-r1';\n  const HK_STALE_MODAL_HARD_GATE_REV='treasure-stale-modal-hard-gate-20260929-r1';\n  const HK_CHEST_LOT_HARD_GATE_REV='chest-lot-hard-gate-20260929-r1';\n  const HK_TREASURE_KEY_GLOBAL_GATE_REV='treasure-key-global-gate-20260929-r1';\n  const HK_BATTLE_OFFSCREEN_ACTION_REV='battle-offscreen-action-scroll-20260929-r1';",
    "revisions")

# ---------------------------------------------------------------------------
# Battle: use the target/action element's own scrollable ancestor, not only the
# fight-grid host. This is required when the confirmation button is below the
# fold inside a modal on 4x3 mobile layouts.
# ---------------------------------------------------------------------------
old_host=r'''    function battleScrollHost() {
      const seed=document.querySelector(
        '[data-lot-id^="mf_treasurelot_sword_"],[data-lot-id*="mf_treasurelot_enemy_type_"],[data-lot-id^="mf_fight_egg_"]'
      );
      let node=seed?.parentElement || null;
'''
new_host=r'''    function battleScrollHost(element=null) {
      const seed=element || document.querySelector(
        '[data-lot-id^="mf_treasurelot_sword_"],[data-lot-id*="mf_treasurelot_enemy_type_"],[data-lot-id^="mf_fight_egg_"]'
      );
      let node=seed?.parentElement || null;
'''
rep(old_host,new_host,"battle scroll host")

rep("        const host=battleScrollHost();",
    "        const host=battleScrollHost(element);",
    "battle target host",
    count=1)

old_action=r'''        const actionButton=await waitBattleActionButton(expectedCost,runId);
        if (!actionButton) {
          recordDiagnostic('battle-auto-stop',{
            revision:HK_BATTLE_RAW_CONTEXT_REV,
            reason:'attack-button-missing',
            slot,
            expectedCost
          });
          return false;
        }
        if (!dispatchBattleOverlaySafeTap(actionButton,'battle-confirm-attack')) {
          recordDiagnostic('battle-auto-stop',{
            revision:HK_BATTLE_RAW_CONTEXT_REV,
            reason:'attack-confirm-tap-failed',
            slot,
            expectedCost
          });
          return false;
        }
'''
new_action=r'''        const actionButton=await waitBattleActionButton(expectedCost,runId);
        if (!actionButton) {
          recordDiagnostic('battle-auto-stop',{
            revision:HK_BATTLE_RAW_CONTEXT_REV,
            reason:'attack-button-missing',
            slot,
            expectedCost
          });
          return false;
        }

        // 4x3 does not fit on many phones. The action button may exist in DOM
        // below the viewport; that is not a missing button. Scroll the correct
        // modal/container until elementFromPoint proves the exact target is
        // clickable, then and only then confirm the attack.
        const actionReady=await battleScrollTargetIntoViewportAsync(
          actionButton,
          'battle-action-slot-'+String(slot),
          runId
        );
        if (!actionReady) {
          recordDiagnostic('battle-auto-stop',{
            revision:HK_BATTLE_OFFSCREEN_ACTION_REV,
            reason:'attack-button-not-clickable-after-scroll',
            slot,
            expectedCost
          });
          return false;
        }
        if (!dispatchBattleOverlaySafeTap(actionButton,'battle-confirm-attack')) {
          recordDiagnostic('battle-auto-stop',{
            revision:HK_BATTLE_RAW_CONTEXT_REV,
            reason:'attack-confirm-tap-failed',
            slot,
            expectedCost
          });
          return false;
        }
'''
rep(old_action,new_action,"battle offscreen action")

# ---------------------------------------------------------------------------
# Chest hard gate: snapshot the exact lot, not the whole room. The next lot is
# forbidden until this exact lot mutates/disappears/activates or a reward/key
# receipt is actually observed and processed.
# ---------------------------------------------------------------------------
auto_vars=r'''    let chestAutoRunning = false;
    let chestAutoRunId = 0;
    let chestAutoToggle = null;
'''
rep(auto_vars,auto_vars+"    let chestPendingLotGate = null;\n","chest pending gate var")

chest_anchor="    async function runTreasureChestAuto() {"
chest_helpers=r'''    function treasureChestLotState(lotId) {
      const wanted=String(lotId||'');
      const rows=[...document.querySelectorAll('[data-lot-id]')]
        .filter(element=>String(element.getAttribute('data-lot-id')||'')===wanted)
        .map(element=>({
          connected:!!element.isConnected,
          text:clean(element.innerText||element.textContent||'').trim(),
          cls:clean(element.className||''),
          activated:/активировано|activated|куплено|purchased|получено|taken|выкуплено|sold\s*out/i.test(
            clean(element.innerText||element.textContent||'')+' '+clean(element.className||'')
          )
        }));

      let unbought=null;
      try { unbought=treasureChestUnboughtCount(wanted); } catch (_) {}
      const keyOffer=treasureChestKeyOfferElements().some(row=>row.lotId===wanted);
      return JSON.stringify({lotId:wanted,rows,unbought,keyOffer});
    }

    function treasureChestPendingConfirmed(gate=chestPendingLotGate) {
      if (!gate) return {ok:true,reason:'no-gate'};
      if (autoMapTreasureKeyModalRoot()) return {ok:false,reason:'treasure-key-modal'};
      if (treasureRewardButton()) return {ok:false,reason:'reward-visible'};
      const current=treasureChestLotState(gate.lotId);
      if (current!==gate.beforeLotState) return {ok:true,reason:'lot-state-changed',current};
      return {ok:false,reason:'lot-state-unchanged',current};
    }

    function treasureChestClearPendingGate(reason='confirmed') {
      const gate=chestPendingLotGate;
      chestPendingLotGate=null;
      recordDiagnostic('chest-lot-hard-gate-clear',{
        revision:HK_CHEST_LOT_HARD_GATE_REV,
        reason,
        lotId:String(gate?.lotId||''),
        ageMs:gate?.startedAt ? Date.now()-gate.startedAt : null
      });
    }

    async function treasureChestResolveGlobalKeyGate(source='chests') {
      const root=autoMapTreasureKeyModalRoot();
      if (!root) return false;
      recordDiagnostic('treasure-key-global-gate',{
        revision:HK_TREASURE_KEY_GLOBAL_GATE_REV,
        source,
        module:'chests'
      });
      const ok=await autoMapBuyTreasureKeyIfPresent();
      if (ok) {
        recordDiagnostic('treasure-key-global-gate-complete',{
          revision:HK_TREASURE_KEY_GLOBAL_GATE_REV,
          source,
          module:'chests'
        });
      }
      return !!ok;
    }

    async function treasureChestReconcilePendingGate() {
      const gate=chestPendingLotGate;
      if (!gate) return true;

      // Global key/reward overlays own the transaction before any other chest
      // can be considered.
      if (autoMapTreasureKeyModalRoot()) {
        const keyDone=await treasureChestResolveGlobalKeyGate('pending-lot');
        if (!keyDone) return false;
        treasureChestClearPendingGate('key-reward-processed');
        return true;
      }

      if (treasureRewardButton()) {
        const rewards=await dismissTreasureRewards(chestAutoRunId);
        if (rewards>0) {
          treasureChestClearPendingGate('reward-processed');
          return true;
        }
        return false;
      }

      const result=treasureChestPendingConfirmed(gate);
      if (result.ok) {
        treasureChestClearPendingGate(result.reason);
        return true;
      }

      const age=Date.now()-gate.startedAt;
      recordDiagnostic('chest-lot-hard-gate-wait',{
        revision:HK_CHEST_LOT_HARD_GATE_REV,
        lotId:gate.lotId,
        ageMs:age,
        reason:result.reason
      });

      // Do not silently move to another lot. After a long unresolved state,
      // stop the owned module rather than spending on an unrelated target.
      if (age>=15000 && autoMapEnabled()) {
        autoMapBlockOwnedModule('chests','lot-state-unconfirmed',30000);
        autoMapStatus('сундук · жду подтверждение',{
          revision:HK_CHEST_LOT_HARD_GATE_REV,
          lotId:gate.lotId
        });
      }
      return false;
    }

'''
if s.count(chest_anchor)!=1:
    raise SystemExit("chest helper anchor missing")
s=s.replace(chest_anchor,chest_helpers+chest_anchor,1)

old_chest_start=r'''    async function runTreasureChestAuto() {
      if (!chestAutoEnabled() || chestAutoRunning || battleAutoRunning) return false;
      if (treasureChestBlockedByForegroundMap()) {
'''
new_chest_start=r'''    async function runTreasureChestAuto() {
      if (!chestAutoEnabled() || chestAutoRunning || battleAutoRunning) return false;

      if (chestPendingLotGate) {
        const reconciled=await treasureChestReconcilePendingGate();
        if (!reconciled) {
          lastSignature='';
          setTimeout(checkPuzzle,480);
          return false;
        }
      }

      if (autoMapTreasureKeyModalRoot()) {
        const keyDone=await treasureChestResolveGlobalKeyGate('runner-preflight');
        if (!keyDone) return false;
        lastSignature='';
        setTimeout(checkPuzzle,120);
        return true;
      }

      if (treasureChestBlockedByForegroundMap()) {
'''
rep(old_chest_start,new_chest_start,"chest runner preflight")

old_before=r'''      const beforeSignature=treasureChestSignature();
      const beforeBalance=walletAmount(target.cost.id);
'''
new_before=r'''      const beforeSignature=treasureChestSignature();
      const beforeLotState=treasureChestLotState(target.lotId);
      const beforeBalance=walletAmount(target.cost.id);
'''
rep(old_before,new_before,"chest before lot snapshot")

old_after_tap=r'''        if (!tapped) {
          recordDiagnostic('chest-auto-stop',{revision:HK_CHEST_AUTO_REV,reason:'action-missing',lotId:target.lotId});
          return false;
        }

        const started=Date.now();
        while (Date.now()-started<CHEST_ACTION_TIMEOUT_MS) {
          if (runId!==chestAutoRunId || !chestAutoEnabled()) return false;
          const changed=treasureChestSignature()!==beforeSignature;
          const reward=treasureRewardButton();
          if (changed || reward || !treasureModalRoot(target.cost)) break;
          await new Promise(resolve=>setTimeout(resolve,100));
        }

        await (target.digging ? chestDigPause('settle',{module:'chests',lotId:target.lotId}) : chestHumanPause('settle',{module:'chests',lotId:target.lotId}));
        const rewards=await dismissTreasureRewards(runId);
'''
new_after_tap=r'''        if (!tapped) {
          recordDiagnostic('chest-auto-stop',{revision:HK_CHEST_AUTO_REV,reason:'action-missing',lotId:target.lotId});
          return false;
        }

        chestPendingLotGate={
          lotId:target.lotId,
          beforeLotState,
          beforeSignature,
          startedAt:Date.now(),
          digging:!!target.digging,
          chest:!!target.chest,
          keyOffer:!!target.keyOffer
        };
        recordDiagnostic('chest-lot-hard-gate-set',{
          revision:HK_CHEST_LOT_HARD_GATE_REV,
          lotId:target.lotId,
          digging:!!target.digging,
          chest:!!target.chest,
          keyOffer:!!target.keyOffer
        });

        let hardConfirmed=false;
        let hardReason='';
        const started=Date.now();
        while (Date.now()-started<Math.max(CHEST_ACTION_TIMEOUT_MS,6500)) {
          if (runId!==chestAutoRunId || !chestAutoEnabled()) return false;

          if (autoMapTreasureKeyModalRoot()) {
            const keyDone=await treasureChestResolveGlobalKeyGate('post-action');
            if (!keyDone) return false;
            hardConfirmed=true;
            hardReason='key-reward-processed';
            break;
          }

          if (treasureRewardButton()) {
            hardConfirmed=true;
            hardReason='reward-visible';
            break;
          }

          const lotState=treasureChestLotState(target.lotId);
          if (lotState!==beforeLotState) {
            hardConfirmed=true;
            hardReason='lot-state-changed';
            break;
          }

          // Whole-room changes are diagnostic only. They are not sufficient to
          // unlock the next lot unless this exact lot or a reward changed.
          const roomChanged=treasureChestSignature()!==beforeSignature;
          if (roomChanged) {
            recordDiagnostic('chest-room-changed-without-lot-confirm',{
              revision:HK_CHEST_LOT_HARD_GATE_REV,
              lotId:target.lotId
            });
          }
          await new Promise(resolve=>setTimeout(resolve,100));
        }

        if (!hardConfirmed) {
          recordDiagnostic('chest-auto-stop',{
            revision:HK_CHEST_LOT_HARD_GATE_REV,
            reason:'lot-state-unconfirmed',
            lotId:target.lotId
          });
          autoMapStatus('сундук · жду подтверждение',{
            revision:HK_CHEST_LOT_HARD_GATE_REV,
            lotId:target.lotId
          });
          return false;
        }

        await (target.digging ? chestDigPause('settle',{module:'chests',lotId:target.lotId}) : chestHumanPause('settle',{module:'chests',lotId:target.lotId}));
        const rewards=await dismissTreasureRewards(runId);
        if (hardReason==='reward-visible' && rewards===0 && treasureRewardButton()) {
          recordDiagnostic('chest-auto-stop',{
            revision:HK_CHEST_LOT_HARD_GATE_REV,
            reason:'reward-not-cleared',
            lotId:target.lotId
          });
          return false;
        }
        treasureChestClearPendingGate(hardReason+(rewards?'-reward-cleared':''));
'''
rep(old_after_tap,new_after_tap,"chest hard confirm")

# ---------------------------------------------------------------------------
# AutoMap transaction diagnostics/gate.
# ---------------------------------------------------------------------------
auto_const_anchor="    const AUTO_MAP_MAX_ACTIONS=240;"
rep(auto_const_anchor,
    auto_const_anchor+"\n    const AUTO_MAP_TXN_PHASES=['IDLE','TARGET_FOUND','CARD_OPENED','ACTION_CONFIRMED','SERVER_UI_STATE_CHANGED','REWARD_CLEARED','ROOM_COMPLETE','EXIT_CONFIRMED','MAP_VISIBLE','NEXT_CELL'];",
    "auto txn phases")

auto_state_anchor=r'''    let autoMapReturnNotBefore=0;
'''
rep(auto_state_anchor,
    auto_state_anchor+"    let autoMapTxn={phase:'IDLE',lotId:'',label:'',updatedAt:Date.now()};\n",
    "auto txn state")

txn_helper_anchor="    function autoMapEnabled() {"
txn_helpers=r'''    function autoMapTxnSet(phase,data={}) {
      const next=String(phase||'IDLE');
      if (!AUTO_MAP_TXN_PHASES.includes(next)) return false;
      const previous=autoMapTxn;
      autoMapTxn={
        phase:next,
        lotId:String(data.lotId ?? previous?.lotId ?? ''),
        label:String(data.label ?? previous?.label ?? ''),
        updatedAt:Date.now()
      };
      recordDiagnostic('treasure-transaction-phase',{
        revision:HK_TREASURE_TXN_GATE_REV,
        from:String(previous?.phase||''),
        to:next,
        lotId:autoMapTxn.lotId,
        label:autoMapTxn.label,
        ...data
      });
      return true;
    }

    function autoMapTxnCanSelectNextCell() {
      return ['IDLE','MAP_VISIBLE','NEXT_CELL'].includes(String(autoMapTxn?.phase||'IDLE'));
    }

    function autoMapTxnMarkMapVisible(source='map-visible') {
      if (!treasureGuideScreenVisible()) return false;
      if (autoMapMiniGameForeground()) return false;
      if (treasureModalRoot(null)) return false;
      autoMapTxnSet('MAP_VISIBLE',{source,lotId:'',label:''});
      return true;
    }

'''
if s.count(txn_helper_anchor)!=1:
    raise SystemExit("txn helper anchor missing")
s=s.replace(txn_helper_anchor,txn_helpers+txn_helper_anchor,1)

# Mark the common confirmation phases.
old_direct=r'''        modal=treasureModalRoot(null);
        if (modal) break;
        if (autoMapStateFingerprint()!==before) return true;
'''
new_direct=r'''        modal=treasureModalRoot(null);
        if (modal) {
          autoMapTxnSet('CARD_OPENED',{label:String(label||''),lotId:autoMapCurrentLot});
          break;
        }
        if (autoMapStateFingerprint()!==before) {
          autoMapTxnSet('SERVER_UI_STATE_CHANGED',{label:String(label||''),lotId:autoMapCurrentLot,mode:'direct'});
          return true;
        }
'''
rep(old_direct,new_direct,"automap card/direct phase")

old_confirm=r'''      if (!dispatchAutoMapTap(action,'auto-map-confirm-'+label)) {
        autoMapRetryNotBefore=Date.now()+1400;
        return false;
      }

      const settleStarted=Date.now();
'''
new_confirm=r'''      if (!dispatchAutoMapTap(action,'auto-map-confirm-'+label)) {
        autoMapRetryNotBefore=Date.now()+1400;
        return false;
      }
      autoMapTxnSet('ACTION_CONFIRMED',{label:String(label||''),lotId:autoMapCurrentLot});

      const settleStarted=Date.now();
'''
rep(old_confirm,new_confirm,"automap action phase")

old_settle=r'''        if (autoMapStateFingerprint()!==before) {
          await minigameHumanPause('settle',{module:'auto-map',label});
          return true;
        }
'''
new_settle=r'''        if (autoMapStateFingerprint()!==before) {
          autoMapTxnSet('SERVER_UI_STATE_CHANGED',{label:String(label||''),lotId:autoMapCurrentLot});
          await minigameHumanPause('settle',{module:'auto-map',label});
          return true;
        }
'''
rep(old_settle,new_settle,"automap server phase")

# Hard stale modal close now verifies disappearance before the map may continue.
old_close=r'''    async function autoMapCloseLingeringModal(reason='stale-modal') {
      if (autoMapMiniGameForeground()) return false;
      const root=treasureModalRoot(null);
      if (!root) return false;
      const close=autoMapModalCloseButton(root);
      if (!close) {
        autoMapStatus('жду окно',{reason});
        return false;
      }
      dispatchAutoMapTap(close,'close-'+reason);
      autoMapLastActionAt=Date.now();
      recordDiagnostic('treasure-auto-map-modal-close',{
        revision:HK_TREASURE_AUTO_MAP_HANDOFF_REV,
        reason
      });
      await new Promise(resolve=>setTimeout(resolve,420));
      return true;
    }
'''
new_close=r'''    async function autoMapCloseLingeringModal(reason='stale-modal') {
      if (autoMapMiniGameForeground()) return false;
      const root=treasureModalRoot(null);
      if (!root) return false;
      let close=autoMapModalCloseButton(root);
      let tapped=false;
      if (close) {
        tapped=dispatchAutoMapTap(close,'close-'+reason);
      } else {
        const rr=root.getBoundingClientRect?.();
        if (rr && rr.width>0 && rr.height>0) {
          tapped=dispatchMinigameOverlaySafeTapAt(
            rr.right-Math.max(18,Math.min(30,rr.width*0.05)),
            rr.top+Math.max(18,Math.min(30,rr.height*0.06)),
            'close-corner-'+reason
          );
        }
      }
      if (!tapped) {
        autoMapStatus('жду окно',{reason});
        return false;
      }

      autoMapLastActionAt=Date.now();
      recordDiagnostic('treasure-auto-map-modal-close',{
        revision:HK_STALE_MODAL_HARD_GATE_REV,
        reason
      });

      const started=Date.now();
      while (Date.now()-started<2600) {
        if (!autoMapEnabled()) return false;
        const current=treasureModalRoot(null);
        if (!current || current!==root) {
          recordDiagnostic('treasure-stale-modal-hard-gate-clear',{
            revision:HK_STALE_MODAL_HARD_GATE_REV,
            reason,
            elapsedMs:Date.now()-started
          });
          return true;
        }
        await new Promise(resolve=>setTimeout(resolve,90));
      }

      autoMapStatus('жду закрытие окна',{reason});
      recordDiagnostic('treasure-stale-modal-hard-gate-block',{
        revision:HK_STALE_MODAL_HARD_GATE_REV,
        reason
      });
      return false;
    }
'''
rep(old_close,new_close,"stale modal hard gate")

# Global treasure-key overlay: no child module may keep running under it.
old_key_preflight=r'''      const keyModal=autoMapTreasureKeyModalRoot();
      if (keyModal && !autoMapModulesRunning()) {
        autoMapRunning=true;
        const keyRunId=autoMapRunId;
        try {
          return await autoMapBuyTreasureKeyIfPresent();
        } finally {
          if (keyRunId===autoMapRunId) autoMapRunning=false;
        }
      }
'''
new_key_preflight=r'''      const keyModal=autoMapTreasureKeyModalRoot();
      if (keyModal) {
        const interrupted=autoMapCancelStaleRunners('treasure-key-global-gate');
        autoMapRunning=true;
        const keyRunId=autoMapRunId;
        autoMapStatus('ключ · завершаю',{
          revision:HK_TREASURE_KEY_GLOBAL_GATE_REV,
          interrupted
        });
        recordDiagnostic('treasure-key-global-gate',{
          revision:HK_TREASURE_KEY_GLOBAL_GATE_REV,
          source,
          interrupted
        });
        try {
          const done=await autoMapBuyTreasureKeyIfPresent();
          if (!done) setTimeout(()=>void runAutoMapTick('treasure-key-global-retry'),420);
          return done;
        } finally {
          if (keyRunId===autoMapRunId) autoMapRunning=false;
        }
      }
'''
rep(old_key_preflight,new_key_preflight,"global key preflight")

# Stale map modal hard gate before selecting/starting any cell.
stale_insert_anchor=r'''      if (Date.now()<autoMapRetryNotBefore) {
        autoMapStatus('пауза');
        return false;
      }
'''
stale_insert=r'''      // A leftover window from a previous action blocks the whole map. Never
      // select another cell underneath it.
      if (
        treasureGuideScreenVisible() &&
        !autoMapMiniGameForeground() &&
        treasureModalRoot(null)
      ) {
        autoMapRunning=true;
        const staleRunId=autoMapRunId;
        try {
          const closed=await autoMapCloseLingeringModal('global-map-preflight');
          if (!closed) {
            setTimeout(()=>void runAutoMapTick('global-stale-modal-retry'),360);
          }
          return !!closed;
        } finally {
          if (staleRunId===autoMapRunId) autoMapRunning=false;
        }
      }

      if (treasureGuideScreenVisible() && !autoMapMiniGameForeground() && !treasureModalRoot(null)) {
        autoMapTxnMarkMapVisible('tick-preflight');
      }

'''
if s.count(stale_insert_anchor)!=1:
    raise SystemExit("stale insert anchor missing")
s=s.replace(stale_insert_anchor,stale_insert+stale_insert_anchor,1)

# Map target selection is physically disabled until the previous transaction
# reached MAP_VISIBLE.
old_target1=r'''            const target=autoMapMapCards()[0];
            if (!target) {
'''
new_target1=r'''            if (!autoMapTxnCanSelectNextCell()) {
              autoMapStatus('жду завершение шага',{
                revision:HK_TREASURE_TXN_GATE_REV,
                phase:autoMapTxn.phase,
                lotId:autoMapTxn.lotId
              });
              return false;
            }
            const target=autoMapMapCards()[0];
            if (!target) {
'''
rep(old_target1,new_target1,"active target gate")

old_target_mark1=r'''            autoMapCurrentLot=target.lotId;
            autoMapStatus('ячейка '+String(target.slot),{
'''
new_target_mark1=r'''            autoMapTxnSet('NEXT_CELL',{lotId:target.lotId,label:'map-cell'});
            autoMapTxnSet('TARGET_FOUND',{lotId:target.lotId,label:'map-cell'});
            autoMapCurrentLot=target.lotId;
            autoMapStatus('ячейка '+String(target.slot),{
'''
rep(old_target_mark1,new_target_mark1,"active target phase")

# There are two target blocks; patch the normal fallback separately.
old_target2=r'''          const target=autoMapMapCards()[0];
          if (target) {
            if (!autoMapSessionStarted()) setAutoMapSessionStarted(true);
'''
new_target2=r'''          if (!autoMapTxnCanSelectNextCell()) {
            autoMapStatus('жду завершение шага',{
              revision:HK_TREASURE_TXN_GATE_REV,
              phase:autoMapTxn.phase,
              lotId:autoMapTxn.lotId
            });
            return false;
          }
          const target=autoMapMapCards()[0];
          if (target) {
            if (!autoMapSessionStarted()) setAutoMapSessionStarted(true);
'''
rep(old_target2,new_target2,"normal target gate")

old_target_mark2=r'''            autoMapCurrentLot=target.lotId;
            autoMapStatus('ячейка '+String(target.slot),{
'''
# First occurrence already replaced, so exactly one remains now.
rep(old_target_mark2,
    r'''            autoMapTxnSet('NEXT_CELL',{lotId:target.lotId,label:'map-cell'});
            autoMapTxnSet('TARGET_FOUND',{lotId:target.lotId,label:'map-cell'});
            autoMapCurrentLot=target.lotId;
            autoMapStatus('ячейка '+String(target.slot),{''',
    "normal target phase",
    count=1)

# Exit handoff phases.
old_exit=r'''      const exit=autoMapExitButton();
      if (exit) {
        autoMapStatus('выход');
        return autoMapTapAndConfirm(exit,'leave-location',10);
      }
'''
new_exit=r'''      const exit=autoMapExitButton();
      if (exit) {
        autoMapTxnSet('ROOM_COMPLETE',{label:'leave-location',lotId:autoMapCurrentLot});
        autoMapStatus('выход');
        const left=await autoMapTapAndConfirm(exit,'leave-location',10);
        if (left) autoMapTxnSet('EXIT_CONFIRMED',{label:'leave-location',lotId:autoMapCurrentLot});
        return left;
      }
'''
rep(old_exit,new_exit,"exit transaction phase")

# checkPuzzle treasure key gate must run even if a child module was active.
rep("      if (autoMapEnabled() && !autoMapModulesRunning() && autoMapTreasureKeyModalRoot()) {",
    "      if (autoMapEnabled() && autoMapTreasureKeyModalRoot()) {",
    "check puzzle global key")

# Export revisions.
export_anchor="      battleActionModalDivRevision:HK_BATTLE_ACTION_MODAL_DIV_REV,"
rep(export_anchor,
    export_anchor+"\n      treasureTransactionGateRevision:HK_TREASURE_TXN_GATE_REV,\n      staleModalHardGateRevision:HK_STALE_MODAL_HARD_GATE_REV,\n      chestLotHardGateRevision:HK_CHEST_LOT_HARD_GATE_REV,\n      treasureKeyGlobalGateRevision:HK_TREASURE_KEY_GLOBAL_GATE_REV,\n      battleOffscreenActionRevision:HK_BATTLE_OFFSCREEN_ACTION_REV,",
    "revision export")

for marker in [
    "// @version      1.18.88",
    "treasure-transaction-gate-20260929-r1",
    "treasure-stale-modal-hard-gate-20260929-r1",
    "chest-lot-hard-gate-20260929-r1",
    "treasure-key-global-gate-20260929-r1",
    "battle-offscreen-action-scroll-20260929-r1",
    "battleScrollHost(element=null)",
    "battle-action-slot-",
    "chestPendingLotGate",
    "treasureChestLotState(",
    "lot-state-unconfirmed",
    "global-map-preflight",
    "autoMapTxnCanSelectNextCell",
    "autoMapTxnSet('ACTION_CONFIRMED'",
    "autoMapCancelStaleRunners('treasure-key-global-gate')",
    "battle-preview-resume-20260929-r1",
    "lights-confirm-ack-before-board-reward-gate-20260928-r1",
    "trader-gold-exact-purchase-modal-20260929-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_TRANSACTION_GATES_1_18_88=PASS")
