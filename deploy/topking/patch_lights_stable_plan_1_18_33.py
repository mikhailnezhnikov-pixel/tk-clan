from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count:
        raise SystemExit(f"{label}: expected {count} got {n}")
    s=s.replace(old,new,count)

rep("// @version      1.18.32",
    "// @version      1.18.33\n// @release-note Лампочки: убран повторный клик подтверждения при медленном ответе сервера — одна покупка теперь отправляется только один раз и затем ждёт ответ до 8 секунд. Автолампы больше не пересчитывают новый маршрут после каждого хода: фиксируется один кратчайший план, каждый фактический переход сверяется с ожидаемой моделью 3×3, а при расхождении автоматизация останавливается вместо кликов туда‑сюда.",
    "version")
rep("const BUILD_VERSION = '1.18.32';",
    "const BUILD_VERSION = '1.18.33';",
    "build")
rep("  const HK_LIGHTS_CONFIRM_VERIFIED_REV='lights-confirm-verified-20260927-r2';",
    "  const HK_LIGHTS_CONFIRM_VERIFIED_REV='lights-confirm-verified-20260927-r2';\n  const HK_LIGHTS_STABLE_PLAN_REV='lights-stable-plan-20260927-r1';",
    "revision")

anchor="""    function lightsNeedsAuto() {
      const board=getLightsBoard();
      if (!Array.isArray(board) || board.length!==9 || board.some(cell=>!cell)) return false;
      const solution=solveLights(board);
      return Array.isArray(solution) && solution.length>0;
    }

"""
helper="""    function lightsState(board = null) {
      const source=board || getLightsBoard();
      if (!Array.isArray(source) || source.length!==9 || source.some(cell=>!cell)) return null;
      return source.map(cell=>!!cell.on);
    }

    function lightsStateKey(state) {
      return Array.isArray(state) && state.length===9
        ? state.map(value=>value?'1':'0').join('')
        : 'INVALID';
    }

    function lightsChangedPositions(beforeState,afterState) {
      const changed=[];
      if (!Array.isArray(beforeState) || !Array.isArray(afterState)) return changed;
      for (let i=0;i<Math.min(beforeState.length,afterState.length);i++) {
        if (!!beforeState[i]!==!!afterState[i]) changed.push(i+1);
      }
      return changed;
    }

    async function waitLightsStableBoard(runId,timeoutMs=2600,stableMs=360) {
      const started=Date.now();
      let lastKey='';
      let stableSince=0;
      while (Date.now()-started<timeoutMs) {
        if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return null;
        const board=getLightsBoard();
        const state=lightsState(board);
        if (!state) {
          await new Promise(resolve=>setTimeout(resolve,90));
          continue;
        }
        const key=lightsStateKey(state);
        if (key!==lastKey) {
          lastKey=key;
          stableSince=Date.now();
        } else if (Date.now()-stableSince>=stableMs) {
          return {board,state,key};
        }
        await new Promise(resolve=>setTimeout(resolve,90));
      }
      const board=getLightsBoard();
      const state=lightsState(board);
      return state ? {board,state,key:lightsStateKey(state)} : null;
    }

"""
if s.count(anchor)!=1:
    raise SystemExit("lightsNeedsAuto anchor missing")
s=s.replace(anchor,anchor+helper,1)

old_confirm="""      const purchaseButton=await waitLightsPurchaseButton(purchaseModal,runId);
      let acknowledgement=null;
      let confirmMode='none';

      if (purchaseButton) {
        const target=lightsPurchaseClickTarget(purchaseButton,purchaseModal);
        acknowledgement=await tryLightsPurchaseAction(
          ()=>dispatchAutoMapTap(target || purchaseButton,'lights-confirm-cost-'+slot),
          purchaseModal,
          before,
          runId,
          slot,
          'clickable-target'
        );
        if (acknowledgement) confirmMode='clickable-target';
      }

      // Dispatching an event is not proof that the game accepted the purchase.
      // Retry only while the same modal remains and the board is unchanged.
      if (!acknowledgement && runId===lightsAutoRunId && lightsAutoEnabled()) {
        const current=lightsModalRoot();
        if (current && current===purchaseModal && lightsBoardSignature()===before) {
          const fresh=lightsPurchaseButton(current) || purchaseButton;
          const target=lightsPurchaseClickTarget(fresh,current);
          if (target) {
            acknowledgement=await tryLightsPurchaseAction(
              ()=>{
                try {
                  if (typeof target.click!=='function') return false;
                  target.click();
                  return true;
                } catch (_) {
                  return false;
                }
              },
              purchaseModal,
              before,
              runId,
              slot,
              'native-click'
            );
            if (acknowledgement) confirmMode='native-click';
          }
        }
      }

      if (!acknowledgement && runId===lightsAutoRunId && lightsAutoEnabled()) {
        const current=lightsModalRoot();
        if (current && current===purchaseModal && lightsBoardSignature()===before) {
          const fresh=lightsPurchaseButton(current) || purchaseButton;
          const rect=fresh?.getBoundingClientRect?.();
          const tap=()=>{
            if (rect && rect.width>0 && rect.height>0) {
              return dispatchBattleTapAt(
                rect.left+rect.width/2,
                rect.top+rect.height/2,
                'lights-confirm-center-'+slot
              );
            }
            return tapLightsPurchaseFallback(current,slot);
          };
          acknowledgement=await tryLightsPurchaseAction(
            tap,
            purchaseModal,
            before,
            runId,
            slot,
            'center-fallback'
          );
          if (acknowledgement) confirmMode='center-fallback';
        }
      }

      if (!acknowledgement) {
        return {ok:false,reason:'purchase-not-accepted'};
      }

      recordDiagnostic('lights-purchase-confirmed',{
        revision:HK_LIGHTS_CONFIRM_VERIFIED_REV,
        slot,
        selector:purchaseButton?'element':'coordinate-fallback',
        mode:confirmMode,
        changed:!!acknowledgement.changed,
        hasAcknowledge:!!acknowledgement.button
      });

      if (!acknowledgement.button && !acknowledgement.changed) {
        acknowledgement=await waitLightsAcknowledge(runId,before);
      }
"""
new_confirm="""      const purchaseButton=await waitLightsPurchaseButton(purchaseModal,runId);
      let fired=false;
      let confirmMode='none';

      if (purchaseButton) {
        const target=lightsPurchaseClickTarget(purchaseButton,purchaseModal) || purchaseButton;
        fired=dispatchAutoMapTap(target,'lights-confirm-cost-'+slot);
        if (fired) confirmMode='single-clickable-target';

        // Native/coordinate fallbacks are allowed only when no click event could
        // be dispatched at all. Never retry merely because the server is slow:
        // a second accepted purchase would toggle the same lamp twice.
        if (!fired) {
          try {
            if (typeof target.click==='function') {
              target.click();
              fired=true;
              confirmMode='single-native-click';
            }
          } catch (_) {}
        }

        if (!fired) {
          const rect=target.getBoundingClientRect?.();
          if (rect && rect.width>0 && rect.height>0) {
            fired=dispatchBattleTapAt(
              rect.left+rect.width/2,
              rect.top+rect.height/2,
              'lights-confirm-center-'+slot
            );
            if (fired) confirmMode='single-center-fallback';
          }
        }
      } else {
        fired=tapLightsPurchaseFallback(purchaseModal,slot);
        if (fired) confirmMode='single-modal-fallback';
      }

      if (!fired) {
        return {ok:false,reason:'purchase-tap-failed'};
      }

      recordDiagnostic('lights-purchase-attempt',{
        revision:HK_LIGHTS_STABLE_PLAN_REV,
        slot,
        mode:confirmMode,
        singleAttempt:true
      });

      // One dispatched purchase gets one server-response window. No second click
      // is sent while the same modal is still waiting for the first request.
      let acknowledgement=await waitLightsAcknowledge(runId,before,8000);
      if (!acknowledgement.button && !acknowledgement.changed) {
        const current=lightsModalRoot();
        if (current && current===purchaseModal && lightsBoardSignature()===before) {
          return {ok:false,reason:'purchase-no-response'};
        }
        acknowledgement={
          button:lightsAcknowledgeButton(current),
          changed:lightsBoardSignature()!==before
        };
      }

      recordDiagnostic('lights-purchase-confirmed',{
        revision:HK_LIGHTS_STABLE_PLAN_REV,
        slot,
        selector:purchaseButton?'element':'coordinate-fallback',
        mode:confirmMode,
        changed:!!acknowledgement.changed,
        hasAcknowledge:!!acknowledgement.button
      });
"""
rep(old_confirm,new_confirm,"single purchase confirmation")

start=s.find("    async function runLightsAuto() {")
end=s.find("\n    function battleElementForSlot",start)
if start<0 or end<0:
    raise SystemExit("runLightsAuto block not found")
old_auto=s[start:end]
new_auto="""    async function runLightsAuto() {
      if (!lightsAutoEnabled() || lightsAutoRunning || battleAutoRunning || chestAutoRunning) return false;
      lightsAutoRunning=true;
      const runId=++lightsAutoRunId;
      let steps=0;
      let plan=null;
      let planIndex=0;
      let expectedState=null;

      recordDiagnostic('lights-auto-start',{revision:HK_LIGHTS_STABLE_PLAN_REV});

      try {
        while (runId===lightsAutoRunId && lightsAutoEnabled()) {
          if (steps>=LIGHTS_AUTO_MAX_STEPS) {
            return failLightsAuto('step-limit',{steps});
          }

          const board=getLightsBoard();
          const valid=board.filter(cell=>cell!==null);
          if (valid.length!==9) {
            if (lightsRewardElement()) {
              const rewardResult=await runLightsFinalReward(runId,steps);
              if (!rewardResult.ok) {
                if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return false;
                return failLightsAuto(rewardResult.reason,{steps,phase:'post-board-replacement'});
              }
              recordDiagnostic('lights-auto-complete',{
                revision:HK_TREASURE_FINAL_REWARD_HANDOFF_REV,
                steps,
                reason:rewardResult.claimed?'post-board-reward-claimed':'post-board-solved'
              });
              if (rewardResult.claimed && autoMapEnabled()) {
                setTimeout(()=>void runAutoMapTick('lights-final-reward-claimed'),minigameRandomMs(700,1200));
              }
              return true;
            }
            if (!getSignature().startsWith('LIGHTS|')) {
              clearNumbers();
              recordDiagnostic('lights-auto-complete',{revision:HK_LIGHTS_STABLE_PLAN_REV,steps,reason:'board-closed'});
              return true;
            }
            return failLightsAuto('board-invalid',{valid:valid.length,steps});
          }

          const currentState=lightsState(board);
          if (!currentState) return failLightsAuto('state-invalid',{steps});
          const before=lightsBoardSignature(board);

          if (plan===null) {
            plan=solveLights(board);
            if (plan===null) {
              return failLightsAuto('solution-missing',{state:before,steps});
            }
            if (plan.length===0) {
              const rewardResult=await runLightsFinalReward(runId,steps);
              if (!rewardResult.ok) {
                if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return false;
                return failLightsAuto(rewardResult.reason,{steps});
              }
              recordDiagnostic('lights-auto-complete',{
                revision:HK_LIGHTS_STABLE_PLAN_REV,
                steps,
                reason:rewardResult.claimed?'solved-and-reward-claimed':'solved'
              });
              return true;
            }

            planIndex=0;
            expectedState=currentState.slice();
            drawLightsSolution(board,plan);
            recordDiagnostic('lights-plan-fixed',{
              revision:HK_LIGHTS_STABLE_PLAN_REV,
              state:lightsStateKey(expectedState),
              plan:plan.map(pos=>pos+1),
              length:plan.length
            });
          } else {
            if (lightsStateKey(currentState)!==lightsStateKey(expectedState)) {
              return failLightsAuto('plan-state-drift',{
                steps,
                expected:lightsStateKey(expectedState),
                actual:lightsStateKey(currentState),
                remainingPlan:plan.slice(planIndex).map(pos=>pos+1)
              });
            }
            drawLightsSolution(board,plan.slice(planIndex));
          }

          if (planIndex>=plan.length) {
            if (!allLightsOn(currentState)) {
              return failLightsAuto('plan-exhausted-not-solved',{
                steps,
                state:lightsStateKey(currentState)
              });
            }
            plan=null;
            continue;
          }

          const position=plan[planIndex];
          const target=board[position]?.element;
          if (!target || !target.isConnected) {
            return failLightsAuto('target-missing',{position,steps});
          }

          const predicted=applyLightPress(currentState,position);
          steps+=1;
          recordDiagnostic('lights-auto-click',{
            revision:HK_LIGHTS_STABLE_PLAN_REV,
            step:steps,
            slot:position+1,
            planIndex,
            fixedPlan:plan.map(pos=>pos+1),
            expectedAfter:lightsStateKey(predicted),
            flow:'fixed-shortest-plan>single-purchase>verify-transition'
          });

          const result=await runLightsModalStep(before,target,position+1,runId);
          if (!result.ok) {
            if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return false;
            return failLightsAuto(result.reason,{
              position,
              slot:position+1,
              steps,
              state:before,
              plan:plan.map(pos=>pos+1)
            });
          }

          await new Promise(resolve=>setTimeout(resolve,LIGHTS_AUTO_SETTLE_MS));
          const stable=await waitLightsStableBoard(runId);
          if (!stable) {
            return failLightsAuto('field-not-stable',{position,slot:position+1,steps});
          }

          const observed=stable.state;
          if (lightsStateKey(observed)!==lightsStateKey(predicted)) {
            return failLightsAuto('transition-mismatch',{
              position,
              slot:position+1,
              steps,
              before:lightsStateKey(currentState),
              expected:lightsStateKey(predicted),
              observed:lightsStateKey(observed),
              expectedChanged:lightsChangedPositions(currentState,predicted),
              observedChanged:lightsChangedPositions(currentState,observed),
              plan:plan.map(pos=>pos+1)
            });
          }

          expectedState=predicted;
          planIndex+=1;

          recordDiagnostic('lights-auto-step-complete',{
            revision:HK_LIGHTS_STABLE_PLAN_REV,
            step:steps,
            slot:position+1,
            planIndex,
            remainingPlan:plan.slice(planIndex).map(pos=>pos+1),
            state:lightsStateKey(observed),
            result:result.reason
          });

          if (planIndex>=plan.length && allLightsOn(observed)) {
            plan=null;
          }
        }
        return false;
      } finally {
        if (runId===lightsAutoRunId) lightsAutoRunning=false;
        lastSignature='';
        setTimeout(checkPuzzle,300);
      }
    }
"""
s=s[:start]+new_auto+s[end:]

rep("      lightsConfirmVerifiedRevision:HK_LIGHTS_CONFIRM_VERIFIED_REV,\n      start,",
    "      lightsConfirmVerifiedRevision:HK_LIGHTS_CONFIRM_VERIFIED_REV,\n      lightsStablePlanRevision:HK_LIGHTS_STABLE_PLAN_REV,\n      start,",
    "export revision")

for marker in [
    "// @version      1.18.33",
    "const BUILD_VERSION = '1.18.33';",
    "lights-stable-plan-20260927-r1",
    "singleAttempt:true",
    "purchase-no-response",
    "function lightsState(",
    "function lightsChangedPositions(",
    "async function waitLightsStableBoard",
    "lights-plan-fixed",
    "fixed-shortest-plan>single-purchase>verify-transition",
    "transition-mismatch",
    "plan-state-drift",
    "lights-confirm-verified-20260927-r2",
    "fishing-zero-cast-exit-20260927-r1",
    "treasure-final-reward-handoff-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("LIGHTS_STABLE_PLAN_1_18_33=PASS")
