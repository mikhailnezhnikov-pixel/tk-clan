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

rep("// @version      1.18.36",
    "// @version      1.18.37\n// @release-note Лампочки: исправлена причина цикла между двумя состояниями. После успешного переключения поля скрипт теперь обязательно закрывает старое окно лампы (Понятно/X) и только после этого открывает следующую лампу; уже открытая модалка больше никогда не подтверждается как новый ход. Несовпадение рассчитанного перехода/цикл теперь останавливают Автолампы вместо бесконечных повторов.",
    "version")
rep("const BUILD_VERSION = '1.18.36';",
    "const BUILD_VERSION = '1.18.37';",
    "build")
rep("  const HK_LIGHTS_COMPLETED_RETURN_REV = 'lights-completed-dom-return-20260927-r2';",
    "  const HK_LIGHTS_COMPLETED_RETURN_REV = 'lights-completed-dom-return-20260927-r2';\n  const HK_LIGHTS_MODAL_STEP_REV = 'lights-close-modal-between-steps-20260927-r1';",
    "revision")

anchor="""    async function waitLightsAcknowledge(runId,before,timeoutMs=3000) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
        if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return {button:null,changed:false};
        const changed=lightsBoardSignature()!==before;
        const root=lightsModalRoot();
        const button=lightsAcknowledgeButton(root);
        if (button) return {button,changed};
        if (changed && !root) return {button:null,changed:true};
        await new Promise(resolve=>setTimeout(resolve,90));
      }
      return {button:null,changed:lightsBoardSignature()!==before};
    }

"""
helper="""    function lightsModalCloseButton(root) {
      if (!root) return null;
      const rr=root.getBoundingClientRect?.();
      if (!rr) return null;
      const candidates=[...root.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
        .filter(element=>
          element &&
          element!==lightsAutoToggle &&
          !element.disabled &&
          element.getAttribute?.('aria-disabled')!=='true' &&
          visible(element)
        )
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const aria=clean(
            element.getAttribute?.('aria-label') ||
            element.getAttribute?.('title') ||
            ''
          ).trim();
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          const style=getComputedStyle(element);
          const actionable=
            element.matches?.('button,[role="button"],a,[onclick]') ||
            !!element.onclick ||
            style.cursor==='pointer';
          const cx=rect.left+rect.width/2;
          const cy=rect.top+rect.height/2;
          const nearTop=cy<=rr.top+rr.height*0.24;
          const nearRight=cx>=rr.left+rr.width*0.72;
          const small=rect.width>0 && rect.width<=90 && rect.height>0 && rect.height<=90;
          let score=0;
          if (actionable) score+=80;
          if (/^(?:×|✕|x)$/i.test(text)) score+=300;
          if (/close|закрыть/i.test(text+' '+aria)) score+=260;
          if (nearTop) score+=100;
          if (nearRight) score+=100;
          if (small) score+=60;
          if (text==='1' || /(?:🫐|🍒|🍓)?\\s*1$/u.test(text)) score-=600;
          if (/^(?:понятно|got it|understood|ok|okay)$/i.test(text)) score-=200;
          return {element,score,rect};
        })
        .filter(row=>row.score>=240)
        .sort((a,b)=>b.score-a.score || a.rect.width*a.rect.height-b.rect.width*b.rect.height);
      return candidates[0]?.element || null;
    }

    async function closeLightsModalAfterStateChange(runId,before,slot,timeoutMs=4200) {
      const started=Date.now();
      let lastActionAt=0;
      let coordinateFallbackUsed=false;

      while (Date.now()-started<timeoutMs) {
        if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return false;

        const changed=lightsBoardSignature()!==before;
        const root=lightsModalRoot();
        if (!root) return changed;

        // Never close/advance before the game actually accepted this lamp press.
        if (!changed) {
          await new Promise(resolve=>setTimeout(resolve,90));
          continue;
        }

        if (Date.now()-lastActionAt<320) {
          await new Promise(resolve=>setTimeout(resolve,90));
          continue;
        }

        const ack=lightsAcknowledgeButton(root);
        if (ack) {
          if (dispatchBattleTap(ack,'lights-understood-after-change-'+slot)) {
            lastActionAt=Date.now();
            recordDiagnostic('lights-modal-drain',{
              revision:HK_LIGHTS_MODAL_STEP_REV,
              slot,
              action:'ack'
            });
            await new Promise(resolve=>setTimeout(resolve,220));
            continue;
          }
        }

        const close=lightsModalCloseButton(root);
        if (close) {
          if (dispatchBattleTap(close,'lights-close-after-change-'+slot)) {
            lastActionAt=Date.now();
            recordDiagnostic('lights-modal-drain',{
              revision:HK_LIGHTS_MODAL_STEP_REV,
              slot,
              action:'close'
            });
            await new Promise(resolve=>setTimeout(resolve,220));
            continue;
          }
        }

        if (!coordinateFallbackUsed) {
          const rr=root.getBoundingClientRect?.();
          if (rr && rr.width>120 && rr.height>120) {
            coordinateFallbackUsed=true;
            const x=rr.left+rr.width-18;
            const y=rr.top+18;
            if (dispatchBattleTapAt(x,y,'lights-close-corner-after-change-'+slot)) {
              lastActionAt=Date.now();
              recordDiagnostic('lights-modal-drain',{
                revision:HK_LIGHTS_MODAL_STEP_REV,
                slot,
                action:'corner-fallback'
              });
              await new Promise(resolve=>setTimeout(resolve,260));
              continue;
            }
          }
        }

        await new Promise(resolve=>setTimeout(resolve,100));
      }

      return lightsBoardSignature()!==before && !lightsModalRoot();
    }

    async function clearStaleLightsModalBeforeStep(runId,slot,timeoutMs=2200) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
        if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return false;
        const root=lightsModalRoot();
        if (!root) return true;

        const ack=lightsAcknowledgeButton(root);
        if (ack && dispatchBattleTap(ack,'lights-clear-stale-ack-'+slot)) {
          recordDiagnostic('lights-stale-modal-cleared',{
            revision:HK_LIGHTS_MODAL_STEP_REV,
            slot,
            method:'ack'
          });
          await new Promise(resolve=>setTimeout(resolve,240));
          continue;
        }

        const close=lightsModalCloseButton(root);
        if (close && dispatchBattleTap(close,'lights-clear-stale-close-'+slot)) {
          recordDiagnostic('lights-stale-modal-cleared',{
            revision:HK_LIGHTS_MODAL_STEP_REV,
            slot,
            method:'close'
          });
          await new Promise(resolve=>setTimeout(resolve,240));
          continue;
        }

        const rr=root.getBoundingClientRect?.();
        if (rr && rr.width>120 && rr.height>120) {
          if (dispatchBattleTapAt(rr.left+rr.width-18,rr.top+18,'lights-clear-stale-corner-'+slot)) {
            recordDiagnostic('lights-stale-modal-cleared',{
              revision:HK_LIGHTS_MODAL_STEP_REV,
              slot,
              method:'corner-fallback'
            });
            await new Promise(resolve=>setTimeout(resolve,260));
            continue;
          }
        }

        await new Promise(resolve=>setTimeout(resolve,100));
      }
      return !lightsModalRoot();
    }

"""
if s.count(anchor)!=1:
    raise SystemExit("waitLightsAcknowledge anchor missing")
s=s.replace(anchor,anchor+helper,1)

# Replace whole modal step with strict one-step-one-modal flow.
start=s.find("    async function runLightsModalStep(before,target,slot,runId) {")
end=s.find("\n    function lightsRewardElement()",start)
if start<0 or end<0:
    raise SystemExit("runLightsModalStep block not found")

new_step="""    async function runLightsModalStep(before,target,slot,runId) {
      if (!target || !target.isConnected) return {ok:false,reason:'target-missing'};

      // A modal left from the previous lamp must never be interpreted as the
      // confirmation window for this new lamp. Drain it first, without pressing 1.
      if (lightsModalRoot()) {
        const cleared=await clearStaleLightsModalBeforeStep(runId,slot);
        if (!cleared) return {ok:false,reason:'stale-modal-blocking'};
      }

      if (runId!==lightsAutoRunId || !lightsAutoEnabled()) {
        return {ok:false,reason:'cancelled'};
      }

      const opened=dispatchAutoMapTap(target,'lights-open-'+slot);
      if (!opened) return {ok:false,reason:'target-tap-failed'};

      const purchaseModal=await waitLightsModal(runId);
      if (!purchaseModal) return {ok:false,reason:'purchase-modal-missing'};

      const purchaseButton=await waitLightsPurchaseButton(purchaseModal,runId);
      let fired=false;
      let confirmMode='none';

      if (purchaseButton) {
        const clickTarget=lightsPurchaseClickTarget(purchaseButton,purchaseModal) || purchaseButton;
        fired=dispatchAutoMapTap(clickTarget,'lights-confirm-cost-'+slot);
        if (fired) confirmMode='single-clickable-target';

        if (!fired) {
          try {
            if (typeof clickTarget.click==='function') {
              clickTarget.click();
              fired=true;
              confirmMode='single-native-click';
            }
          } catch (_) {}
        }

        if (!fired) {
          const rect=clickTarget.getBoundingClientRect?.();
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

      if (!fired) return {ok:false,reason:'purchase-tap-failed'};

      recordDiagnostic('lights-purchase-attempt',{
        revision:HK_LIGHTS_MODAL_STEP_REV,
        slot,
        mode:confirmMode,
        singleAttempt:true
      });

      // First wait only for the board itself to change. Do not return to the
      // planner while any lamp modal is still open.
      const changed=await waitLightsBoardChange(before,runId);
      if (!changed) return {ok:false,reason:'field-no-change'};

      const drained=await closeLightsModalAfterStateChange(runId,before,slot);
      if (!drained) {
        return {ok:false,reason:'modal-not-closed-after-change'};
      }

      recordDiagnostic('lights-auto-step-ui-complete',{
        revision:HK_LIGHTS_MODAL_STEP_REV,
        slot,
        mode:confirmMode,
        state:lightsBoardSignature()
      });
      return {ok:true,reason:'field-changed-modal-closed'};
    }
"""
s=s[:start]+new_step+s[end:]

# Make logical mismatches fatal instead of infinite AutoMap recover loops.
old_fail="""      if (autoMapOwnsLights) {
        // A single DOM timing miss must not permanently disable the module while
        // full AutoMap is responsible for the room. Keep it armed and retry after
        // a human-sized pause; runLightsModalStep can resume an already-open modal.
        try { localStorage.setItem(LIGHTS_AUTO_STORAGE_KEY,'1'); } catch (_) {}
        updateLightsAutoToggle();
        recordDiagnostic('lights-auto-recover',{
          revision:HK_LIGHTS_CONFIRM_RECOVERY_REV,
          reason,
          ...data
        });
        setTimeout(()=>{
          lastSignature='';
          checkPuzzle();
        },minigameRandomMs(900,1400));
        return false;
      }

      try { localStorage.setItem(LIGHTS_AUTO_STORAGE_KEY,'0'); } catch (_) {}
"""
new_fail="""      const fatalReasons=new Set([
        'state-cycle',
        'transition-mismatch',
        'plan-state-drift',
        'plan-exhausted-not-solved',
        'step-limit',
        'stale-modal-blocking',
        'modal-not-closed-after-change'
      ]);

      if (autoMapOwnsLights && !fatalReasons.has(reason)) {
        // Timing/network misses may be retried, but mathematical/state-machine
        // mismatches must never spend berries in an endless two-state loop.
        try { localStorage.setItem(LIGHTS_AUTO_STORAGE_KEY,'1'); } catch (_) {}
        updateLightsAutoToggle();
        recordDiagnostic('lights-auto-recover',{
          revision:HK_LIGHTS_MODAL_STEP_REV,
          reason,
          ...data
        });
        setTimeout(()=>{
          lastSignature='';
          checkPuzzle();
        },minigameRandomMs(1100,1700));
        return false;
      }

      try { localStorage.setItem(LIGHTS_AUTO_STORAGE_KEY,'0'); } catch (_) {}
"""
rep(old_fail,new_fail,"fatal mismatch stop")

# Diagnostics revision for stops.
rep("      recordDiagnostic('lights-auto-stop',{revision:HK_LIGHTS_AUTO_REV,reason,...data});",
    "      recordDiagnostic('lights-auto-stop',{revision:HK_LIGHTS_MODAL_STEP_REV,reason,...data});",
    "stop revision")

rep("      lightsCompletedReturnRevision:HK_LIGHTS_COMPLETED_RETURN_REV,\n      start,",
    "      lightsCompletedReturnRevision:HK_LIGHTS_COMPLETED_RETURN_REV,\n      lightsModalStepRevision:HK_LIGHTS_MODAL_STEP_REV,\n      start,",
    "export modal step revision")

for marker in [
    "// @version      1.18.37",
    "const BUILD_VERSION = '1.18.37';",
    "lights-close-modal-between-steps-20260927-r1",
    "function lightsModalCloseButton(root)",
    "async function closeLightsModalAfterStateChange",
    "async function clearStaleLightsModalBeforeStep",
    "stale-modal-blocking",
    "modal-not-closed-after-change",
    "field-changed-modal-closed",
    "fatalReasons=new Set",
    "transition-mismatch",
    "lights-completed-dom-return-20260927-r2",
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("LIGHTS_MODAL_STEP_1_18_37=PASS")
