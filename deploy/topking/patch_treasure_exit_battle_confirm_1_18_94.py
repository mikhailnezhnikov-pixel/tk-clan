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

rep("// @version      1.18.93",
    "// @version      1.18.94\n// @release-note Карта сокровищ: Охота за сундуками больше не зависает на недоступном оставшемся сундуке — если раскопки завершены, доступных сундуков/ключей для покупки нет, комната считается исчерпанной и Автокарта нажимает выход. Сражение: уже открытая карточка противника теперь имеет абсолютный приоритет — Автобой подтверждает нижнюю кнопку стоимости прямо в открытой модалке, не требуя видимости заголовка Сражение под затемнением.",
    "version")
rep("const BUILD_VERSION = '1.18.93';",
    "const BUILD_VERSION = '1.18.94';",
    "build")

rev_anchor="  const HK_CHEST_UNCOMMITTED_RETRY_REV='chest-uncommitted-retry-20260929-r1';"
rep(rev_anchor,
    rev_anchor+"\n  const HK_CHEST_EXHAUSTED_EXIT_REV='chest-exhausted-exit-20260930-r1';\n  const HK_BATTLE_OPEN_MODAL_CONFIRM_REV='battle-open-modal-confirm-20260930-r1';",
    "new revisions")

old_block=r'''        const dependency=keyOffers[0] || null;
        return {
          phase:dependency?'chest-key':'chest',
          pending:chestRows.length,
          affordable:0,
          target:dependency ? {...dependency,phase:'chest-key'} : null,
          rows,
          diggingRows,
          chestRows,
          keyOffers
        };'''
new_block=r'''        const dependency=keyOffers[0] || null;
        if (dependency) {
          return {
            phase:'chest-key',
            pending:chestRows.length,
            affordable:0,
            target:{...dependency,phase:'chest-key'},
            rows,
            diggingRows,
            chestRows,
            keyOffers,
            exhausted:false
          };
        }

        // A visible chest may remain on the board even though the player has no
        // matching key and the room offers no affordable way to obtain one.
        // That is not unfinished actionable work. Waiting here forever blocks
        // the entire Treasure Map. Once digging is finished and no chest/key
        // action can be performed, hand the room back to AutoMap so it can exit.
        return {
          phase:'done',
          pending:0,
          affordable:0,
          target:null,
          rows,
          diggingRows,
          chestRows,
          keyOffers,
          exhausted:true,
          exhaustedChestCount:chestRows.length,
          reason:'no-affordable-chest-or-key'
        };'''
rep(old_block,new_block,"chest exhausted state")

old_auto=r'''          if (work.target) {
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
          return true;'''
new_auto=r'''          if (work.target) {
            lastSignature='';
            setTimeout(checkPuzzle,20);
          } else if (work.pending>0) {
            // Strict order remains for actually actionable earlier phases.
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
            if (work.exhausted) {
              recordDiagnostic('treasure-chest-exhausted-exit',{
                revision:HK_CHEST_EXHAUSTED_EXIT_REV,
                reason:String(work.reason||''),
                skippedUnaffordable:Number(work.exhaustedChestCount||0),
                diggingPending:work.diggingRows.length,
                keyOffers:work.keyOffers.length
              });
              autoMapStatus('сундуки → выход',{
                revision:HK_CHEST_EXHAUSTED_EXIT_REV,
                skippedUnaffordable:Number(work.exhaustedChestCount||0)
              });
            }
            const left=await autoMapHandleExitOrContinue();
            if (!left) {
              setTimeout(()=>void runAutoMapTick('chest-exhausted-exit-retry'),560);
            }
          }
          return true;'''
rep(old_auto,new_auto,"automap exhausted chest exit")

old_modal_head=r'''    function battleEnemyModalActionButton(expectedCost) {
      const costText=String(expectedCost ?? '');
      if (!costText || !battleScreenVisiblyCurrent()) return null;
      const exactCost=new RegExp('(?:^|\\s)'+costText+'(?:\\s|$)');
'''
new_modal_head=r'''    function battleEnemyModalActionButton(expectedCost) {
      const costText=String(expectedCost ?? '');
      if (!costText) return null;
      const exactCost=new RegExp('(?:^|\\s)'+costText+'(?:\\s|$)');
'''
rep(old_modal_head,new_modal_head,"battle modal no title gate")

old_root_tail=r'''      const root=roots[0]?.element || null;
      if (!root) return null;
      const rr=root.getBoundingClientRect?.();
'''
new_root_tail=r'''      const root=roots[0]?.element || null;
      if (!root) return null;
      const rr=root.getBoundingClientRect?.();
'''
# anchor retained intentionally; assert uniqueness
if s.count(old_root_tail)!=1:
    raise SystemExit(f"battle modal root anchor expected 1 got {s.count(old_root_tail)}")

insert_anchor=r'''    function battleActionButton(expectedCost) {'''
helper=r'''    function battleEnemyModalRoot() {
      const roots=[...document.querySelectorAll(
        '[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"],div'
      )]
        .filter(visible)
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          return {element,text,rect,area:rect.width*rect.height};
        })
        .filter(row=>/МОЖНО\s+ОТЫСКАТЬ|CAN\s+BE\s+FOUND/i.test(row.text))
        .filter(row=>row.rect.width>=Math.min(260,window.innerWidth*0.40) && row.rect.height>=220)
        .filter(row=>row.rect.width<=window.innerWidth*0.99 && row.rect.height<=window.innerHeight*0.98)
        .sort((a,b)=>a.area-b.area);
      return roots[0]?.element || null;
    }

    async function battleConfirmAlreadyOpenEnemyModal(expectedCost,runId,beforeSignature=null) {
      const root=battleEnemyModalRoot();
      if (!root) return {handled:false,success:false,reason:'no-modal'};

      const action=battleEnemyModalActionButton(expectedCost);
      if (!action) {
        recordDiagnostic('battle-open-modal-confirm-wait',{
          revision:HK_BATTLE_OPEN_MODAL_CONFIRM_REV,
          expectedCost:Number(expectedCost),
          reason:'action-missing'
        });
        return {handled:true,success:false,reason:'action-missing'};
      }

      const before=beforeSignature===null ? getSignature() : beforeSignature;
      const beforeSwords=Number(getBattleAttack());
      const ready=await battleScrollTargetIntoViewportAsync(
        action,
        'battle-open-modal-confirm-'+String(expectedCost),
        runId
      );
      if (!ready) {
        recordDiagnostic('battle-open-modal-confirm-stop',{
          revision:HK_BATTLE_OPEN_MODAL_CONFIRM_REV,
          expectedCost:Number(expectedCost),
          reason:'action-not-clickable'
        });
        return {handled:true,success:false,reason:'action-not-clickable'};
      }

      let sent=dispatchBattleOverlaySafeTap(action,'battle-open-modal-confirm');
      if (!sent && root.isConnected) {
        const rr=root.getBoundingClientRect?.();
        if (rr && rr.width>0 && rr.height>0) {
          for (const fraction of [0.91,0.87,0.94]) {
            if (runId!==battleAutoRunId || !battleAutoEnabled()) {
              return {handled:true,success:false,reason:'cancelled'};
            }
            sent=dispatchBattleOverlaySafeTapAt(
              rr.left+rr.width/2,
              rr.top+rr.height*fraction,
              'battle-open-modal-confirm-fallback-'+String(fraction)
            );
            if (sent) break;
          }
        }
      }
      if (!sent) {
        return {handled:true,success:false,reason:'tap-failed'};
      }

      const started=Date.now();
      while (Date.now()-started<4400) {
        if (runId!==battleAutoRunId || !battleAutoEnabled()) {
          return {handled:true,success:false,reason:'cancelled'};
        }
        const currentRoot=battleEnemyModalRoot();
        const currentSwords=Number(getBattleAttack());
        const currentSignature=getSignature();
        if (!currentRoot || currentRoot!==root || currentSignature!==before ||
            (Number.isFinite(beforeSwords) && Number.isFinite(currentSwords) && currentSwords!==beforeSwords)) {
          recordDiagnostic('battle-open-modal-confirm-complete',{
            revision:HK_BATTLE_OPEN_MODAL_CONFIRM_REV,
            expectedCost:Number(expectedCost),
            modalClosed:!currentRoot || currentRoot!==root,
            signatureChanged:currentSignature!==before,
            swordsBefore:beforeSwords,
            swordsAfter:currentSwords
          });
          return {handled:true,success:true,reason:'accepted'};
        }
        await new Promise(resolve=>setTimeout(resolve,90));
      }

      recordDiagnostic('battle-open-modal-confirm-stop',{
        revision:HK_BATTLE_OPEN_MODAL_CONFIRM_REV,
        expectedCost:Number(expectedCost),
        reason:'no-state-change'
      });
      return {handled:true,success:false,reason:'no-state-change'};
    }

'''
if s.count(insert_anchor)!=1:
    raise SystemExit("battle action insert anchor missing")
s=s.replace(insert_anchor,helper+insert_anchor,1)

runner_anchor=r'''        const expectedCost=battleCostForElement(element);
        const targetProbe=battleElementTapProbe(element);
        if (!targetProbe.ready) {
          recordDiagnostic('battle-auto-stop',{
            revision:HK_BATTLE_TARGET_SCROLL_REV,
            reason:'target-not-clickable-after-scroll',
            slot,
            expectedCost,
            probeReason:targetProbe.reason,
            blockerTag:targetProbe.leafTag||'',
            blockerText:targetProbe.leafText||''
          });
          return false;
        }
        const before=getSignature();
'''
runner_new=r'''        const expectedCost=battleCostForElement(element);

        // If the enemy card is already open (the exact state shown on mobile
        // after AutoMap enters the room), confirming its cost button outranks
        // trying to click the obscured board card again.
        const preOpened=await battleConfirmAlreadyOpenEnemyModal(expectedCost,runId);
        if (preOpened.handled) {
          if (!preOpened.success) {
            recordDiagnostic('battle-auto-stop',{
              revision:HK_BATTLE_OPEN_MODAL_CONFIRM_REV,
              reason:'open-modal-confirm-failed',
              detail:preOpened.reason,
              slot,
              expectedCost
            });
            return false;
          }
          await new Promise(resolve=>setTimeout(resolve,BATTLE_AUTO_SETTLE_MS));
          await dismissBattleRewardIfPresent(runId);
          recordDiagnostic('battle-auto-step-complete',{
            revision:HK_BATTLE_OPEN_MODAL_CONFIRM_REV,
            slot,
            expectedCost,
            source:'already-open-modal'
          });
          return true;
        }

        const targetProbe=battleElementTapProbe(element);
        if (!targetProbe.ready) {
          recordDiagnostic('battle-auto-stop',{
            revision:HK_BATTLE_TARGET_SCROLL_REV,
            reason:'target-not-clickable-after-scroll',
            slot,
            expectedCost,
            probeReason:targetProbe.reason,
            blockerTag:targetProbe.leafTag||'',
            blockerText:targetProbe.leafText||''
          });
          return false;
        }
        const before=getSignature();
'''
rep(runner_anchor,runner_new,"battle already-open modal preflight")

post_click_old=r'''        const actionButton=await waitBattleActionButton(expectedCost,runId);
        if (!actionButton) {
          recordDiagnostic('battle-auto-stop',{
            revision:HK_BATTLE_RAW_CONTEXT_REV,
            reason:'attack-button-missing',
            slot,
            expectedCost
          });
          return false;
        }
'''
post_click_new=r'''        const directModal=await battleConfirmAlreadyOpenEnemyModal(expectedCost,runId,before);
        if (directModal.handled) {
          if (!directModal.success) {
            recordDiagnostic('battle-auto-stop',{
              revision:HK_BATTLE_OPEN_MODAL_CONFIRM_REV,
              reason:'attack-modal-confirm-failed',
              detail:directModal.reason,
              slot,
              expectedCost
            });
            return false;
          }
          await new Promise(resolve=>setTimeout(resolve,BATTLE_AUTO_SETTLE_MS));
          await dismissBattleRewardIfPresent(runId);
          recordDiagnostic('battle-auto-step-complete',{
            revision:HK_BATTLE_OPEN_MODAL_CONFIRM_REV,
            slot,
            expectedCost,
            source:'opened-modal'
          });
          return true;
        }

        const actionButton=await waitBattleActionButton(expectedCost,runId);
        if (!actionButton) {
          recordDiagnostic('battle-auto-stop',{
            revision:HK_BATTLE_RAW_CONTEXT_REV,
            reason:'attack-button-missing',
            slot,
            expectedCost
          });
          return false;
        }
'''
rep(post_click_old,post_click_new,"battle modal confirm after card click")

export_anchor="      chestUncommittedRetryRevision:HK_CHEST_UNCOMMITTED_RETRY_REV,"
rep(export_anchor,
    export_anchor+"\n      chestExhaustedExitRevision:HK_CHEST_EXHAUSTED_EXIT_REV,\n      battleOpenModalConfirmRevision:HK_BATTLE_OPEN_MODAL_CONFIRM_REV,",
    "debug revisions")

p.write_text(s,encoding="utf-8")
print("PATCH_TREASURE_EXIT_BATTLE_CONFIRM_1_18_94=PASS")
