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

def replace_between(start,end,new,label):
    global s
    a=s.find(start)
    if a<0:
        raise SystemExit(f"{label}: start anchor missing")
    b=s.find(end,a+len(start))
    if b<0:
        raise SystemExit(f"{label}: end anchor missing")
    s=s[:a]+new+s[b:]

rep("// @version      1.18.92",
    "// @version      1.18.93\n// @release-note Охота за сундуками: введён жёсткий порядок — сначала раскопать все видимые клетки с красным флагом, затем открыть найденные сундуки, и только после этого переходить к ключам/пост-действиям и возврату на карту. Видимая раскопка теперь важнее backend is_bought. Если подтверждение клика не изменило ни конкретный lot, ни баланс, hard-gate безопасно откатывается как неотправленная транзакция вместо вечного «жду подтверждение».",
    "version")
rep("const BUILD_VERSION = '1.18.92';",
    "const BUILD_VERSION = '1.18.93';",
    "build")

rev_anchor="  const HK_CHEST_VISIBLE_CLAIM_REV='chest-visible-claim-priority-20260928-r1';"
rep(rev_anchor,
    rev_anchor+"\n  const HK_CHEST_PHASE_ORDER_REV='chest-phase-order-20260929-r1';\n  const HK_CHEST_UNCOMMITTED_RETRY_REV='chest-uncommitted-retry-20260929-r1';",
    "chest phase revisions")

target_start="    function treasureChestTarget() {"
target_end="    function treasureCenteredModalRoot() {"
target_block=r'''    function treasureChestDigVisualPending(row) {
      if (!row || row.activated) return false;
      const lotId=String(row.lotId||'');
      if (!/^mf_treasurelot_chest_digging_spot_sl\d+$/.test(lotId)) return false;

      // The visible card is authoritative here. A completed hole has no berry
      // price/footer, while an unfinished red-flag card still exposes a price
      // (normally 5) or the treasure-energy asset.
      const text=String(row.text||clean(row.element?.innerText||row.element?.textContent||'')).trim();
      if (/(?:^|\s)\d{1,4}(?:\s|$)/.test(text)) return true;
      const assets=[...row.element?.querySelectorAll?.('img')||[]]
        .map(img=>String(img.alt||'')+' '+String(img.src||'')).join(' ').toLowerCase();
      return /item_treasurehunt_energy|treasurehunt_energy|digging[^\s]*flag|flag[^\s]*digging/i.test(assets);
    }

    function treasureChestWorkState() {
      const rows=treasureChestElements().filter(row=>!row.activated);
      const diggingRows=rows.filter(treasureChestDigVisualPending);
      const chestRows=rows.filter(row=>/^mf_treasurelot_chest_type_[a-z0-9]+$/i.test(String(row.lotId||'')));
      const keyOffers=treasureChestKeyOfferElements();

      // PHASE 1 — DIG EVERYTHING. As long as even one unfinished red-flag
      // digging card is visible, no chest and no key-offer can pre-empt it.
      if (diggingRows.length) {
        const candidates=diggingRows
          .map((row,index)=>({
            ...row,
            cost:treasureChestVisibleCost(row),
            digging:true,
            chest:false,
            keyOffer:false,
            phase:'dig',
            index
          }))
          .filter(row=>row.cost && treasureChestAffordable(row.cost));
        return {
          phase:'dig',
          pending:diggingRows.length,
          affordable:candidates.length,
          target:candidates[0] || null,
          rows,
          diggingRows,
          chestRows,
          keyOffers
        };
      }

      // PHASE 2 — OPEN CHESTS. This phase is unreachable while a visible
      // unfinished digging card exists. If a chest needs a key and no chest is
      // currently affordable, a standalone key offer may be used only as a
      // dependency for this chest phase; selection returns to chests immediately.
      if (chestRows.length) {
        const candidates=chestRows
          .map((row,index)=>{
            const lotId=String(row.lotId||'');
            let rank=0;
            if (lotId==='mf_treasurelot_chest_type_03') rank=60;
            else if (lotId==='mf_treasurelot_chest_type_02') rank=50;
            else if (lotId==='mf_treasurelot_chest_type_015') rank=40;
            else if (lotId==='mf_treasurelot_chest_type_01') rank=30;
            return {
              ...row,
              cost:treasureChestVisibleCost(row),
              digging:false,
              chest:true,
              keyOffer:false,
              phase:'chest',
              rank,
              index
            };
          })
          .filter(row=>row.cost && treasureChestAffordable(row.cost))
          .sort((a,b)=>b.rank-a.rank || a.index-b.index);

        if (candidates.length) {
          return {
            phase:'chest',
            pending:chestRows.length,
            affordable:candidates.length,
            target:candidates[0],
            rows,
            diggingRows,
            chestRows,
            keyOffers
          };
        }

        const dependency=keyOffers[0] || null;
        return {
          phase:dependency?'chest-key':'chest',
          pending:chestRows.length,
          affordable:0,
          target:dependency ? {...dependency,phase:'chest-key'} : null,
          rows,
          diggingRows,
          chestRows,
          keyOffers
        };
      }

      // PHASE 3 — POST ACTIONS. Only after all digging and all visible chests
      // are finished may an extra standalone key/reward card be collected.
      if (keyOffers.length) {
        return {
          phase:'post',
          pending:keyOffers.length,
          affordable:keyOffers.length,
          target:{...keyOffers[0],phase:'post'},
          rows,
          diggingRows,
          chestRows,
          keyOffers
        };
      }

      return {
        phase:'done',
        pending:0,
        affordable:0,
        target:null,
        rows,
        diggingRows,
        chestRows,
        keyOffers
      };
    }

    function treasureChestTarget() {
      const state=treasureChestWorkState();
      const selected=state.target || null;

      recordDiagnostic('treasure-chest-phase-state',{
        revision:HK_CHEST_PHASE_ORDER_REV,
        phase:state.phase,
        pending:state.pending,
        affordable:state.affordable,
        diggingPending:state.diggingRows.length,
        chestPending:state.chestRows.length,
        keyOffers:state.keyOffers.length,
        selectedLotId:String(selected?.lotId||'')
      });

      if (selected?.chest) {
        recordDiagnostic('treasure-chest-visible-claim-target',{
          revision:HK_CHEST_VISIBLE_CLAIM_REV,
          lotId:selected.lotId,
          cost:selected.cost,
          phase:state.phase,
          remainingDigging:state.diggingRows.length
        });
      }

      if (!selected && state.rows.some(row=>row.activated)) {
        recordDiagnostic('treasure-chest-no-target-after-activated',{
          revision:HK_TREASURE_CHEST_ELEMENT_STATE_REV,
          phase:state.phase,
          activated:state.rows.filter(row=>row.activated).map(row=>({
            lotId:row.lotId,
            text:row.text,
            x:row.x,
            y:row.y
          })).slice(0,12),
          visible:state.rows.map(row=>({
            lotId:row.lotId,
            text:row.text,
            activated:row.activated,
            x:row.x,
            y:row.y
          })).slice(0,24)
        });
      }
      return selected;
    }

'''
replace_between(target_start,target_end,target_block,"chest target state machine")

pending_anchor=r'''    function treasureChestClearPendingGate(reason='confirmed') {'''
pending_helper=r'''    function treasureChestUncommittedRollback(gate=chestPendingLotGate) {
      if (!gate) return {ok:false,reason:'no-gate'};
      const age=Date.now()-Number(gate.startedAt||0);
      if (age<9000) return {ok:false,reason:'grace',ageMs:age};
      if (autoMapTreasureKeyModalRoot()) return {ok:false,reason:'treasure-key-modal',ageMs:age};
      if (treasureRewardButton()) return {ok:false,reason:'reward-visible',ageMs:age};
      if (treasureModalRoot(gate.cost||null)) return {ok:false,reason:'action-modal-visible',ageMs:age};

      const current=treasureChestLotState(gate.lotId);
      if (current!==gate.beforeLotState) return {ok:false,reason:'lot-state-changed',ageMs:age};

      const itemId=String(gate?.cost?.id||'');
      const before=Number(gate?.beforeBalance);
      const now=itemId ? Number(walletAmount(itemId)) : NaN;
      if (!itemId || !Number.isFinite(before) || !Number.isFinite(now)) {
        return {ok:false,reason:'balance-unknown',ageMs:age};
      }
      if (now!==before) return {ok:false,reason:'balance-changed',ageMs:age,beforeBalance:before,afterBalance:now};

      // Same exact lot + same wallet + no modal/reward after the grace window
      // means the confirmation never committed. Clearing the gate is safe and
      // lets the phase machine retry without skipping to another lot.
      return {
        ok:true,
        reason:'action-not-committed',
        ageMs:age,
        beforeBalance:before,
        afterBalance:now,
        current
      };
    }

'''
if s.count(pending_anchor)!=1:
    raise SystemExit("pending clear anchor missing")
s=s.replace(pending_anchor,pending_helper+pending_anchor,1)

reconcile_old=r'''      const age=Date.now()-gate.startedAt;
      recordDiagnostic('chest-lot-hard-gate-wait',{
'''
reconcile_new=r'''      const rollback=treasureChestUncommittedRollback(gate);
      if (rollback.ok) {
        recordDiagnostic('chest-lot-uncommitted-rollback',{
          revision:HK_CHEST_UNCOMMITTED_RETRY_REV,
          lotId:gate.lotId,
          phase:String(gate.phase||''),
          ageMs:rollback.ageMs,
          beforeBalance:rollback.beforeBalance,
          afterBalance:rollback.afterBalance
        });
        treasureChestClearPendingGate(rollback.reason);
        return true;
      }

      const age=Date.now()-gate.startedAt;
      recordDiagnostic('chest-lot-hard-gate-wait',{
'''
rep(reconcile_old,reconcile_new,"pending rollback reconcile")

gate_old=r'''        chestPendingLotGate={
          lotId:target.lotId,
          beforeLotState,
          beforeSignature,
          startedAt:Date.now(),
          digging:!!target.digging,
          chest:!!target.chest,
          keyOffer:!!target.keyOffer
        };'''
gate_new=r'''        chestPendingLotGate={
          lotId:target.lotId,
          beforeLotState,
          beforeSignature,
          beforeBalance,
          cost:target.cost ? {...target.cost} : null,
          phase:String(target.phase||''),
          startedAt:Date.now(),
          digging:!!target.digging,
          chest:!!target.chest,
          keyOffer:!!target.keyOffer
        };'''
rep(gate_old,gate_new,"pending gate receipt")

diag_old=r'''        keyOffer:!!target.keyOffer
      });'''
diag_new=r'''        keyOffer:!!target.keyOffer,
        phase:String(target.phase||'')
      });'''
# only replace the first chest-auto-start diagnostic occurrence
rep(diag_old,diag_new,"chest start phase",1)

automap_old=r'''        if (signature.startsWith('CHESTS|')) {
          autoMapStatus('сундуки');
          if (treasureChestTarget()) {
            lastSignature='';
            setTimeout(checkPuzzle,20);
          } else {
            await autoMapHandleExitOrContinue();
          }
          return true;
        }'''
automap_new=r'''        if (signature.startsWith('CHESTS|')) {
          const work=treasureChestWorkState();
          const phaseLabel=
            work.phase==='dig' ? 'сундуки → раскопка' :
            work.phase==='chest' || work.phase==='chest-key' ? 'сундуки → открыть' :
            work.phase==='post' ? 'сундуки → награды/ключи' :
            'сундуки → готово';
          autoMapStatus(phaseLabel,{
            revision:HK_CHEST_PHASE_ORDER_REV,
            phase:work.phase,
            pending:work.pending,
            affordable:work.affordable,
            diggingPending:work.diggingRows.length,
            chestPending:work.chestRows.length
          });

          if (work.target) {
            lastSignature='';
            setTimeout(checkPuzzle,20);
          } else if (work.pending>0) {
            // Strict order: never leave the room or jump to a chest while an
            // earlier phase still has visible unfinished work.
            autoMapStatus(
              work.phase==='dig' ? 'раскопка · жду ресурс' : 'сундук · жду ресурс',
              {
                revision:HK_CHEST_PHASE_ORDER_REV,
                phase:work.phase,
                pending:work.pending
              }
            );
            setTimeout(()=>void runAutoMapTick('chest-phase-wait'),720);
          } else {
            await autoMapHandleExitOrContinue();
          }
          return true;
        }'''
rep(automap_old,automap_new,"automap chest phase gate")

export_anchor="      chestVisibleClaimRevision:HK_CHEST_VISIBLE_CLAIM_REV,"
rep(export_anchor,
    export_anchor+"\n      chestPhaseOrderRevision:HK_CHEST_PHASE_ORDER_REV,\n      chestUncommittedRetryRevision:HK_CHEST_UNCOMMITTED_RETRY_REV,",
    "debug export")

p.write_text(s,encoding="utf-8")
print("PATCH_CHEST_PHASE_ORDER_1_18_93=PASS")
