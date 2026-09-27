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

rep("// @version      1.18.31",
    "// @version      1.18.32\n// @release-note Лампочки: подтверждение покупки теперь считается успешным только после реального изменения интерфейса. Скрипт поднимается от вложенного текста 1 к настоящему кликабельному контейнеру, проверяет результат после каждого нажатия и только при отсутствии реакции пробует native click и точечный fallback по центру кнопки. Повторная покупка не выполняется, если модалка уже сменилась или поле изменилось.",
    "version")
rep("const BUILD_VERSION = '1.18.31';",
    "const BUILD_VERSION = '1.18.32';",
    "build")
rep("  const HK_LIGHTS_CONFIRM_RECOVERY_REV='lights-confirm-recovery-20260927-r1';",
    "  const HK_LIGHTS_CONFIRM_RECOVERY_REV='lights-confirm-recovery-20260927-r1';\n  const HK_LIGHTS_CONFIRM_VERIFIED_REV='lights-confirm-verified-20260927-r2';",
    "revision")

anchor="""    async function waitLightsPurchaseButton(root,runId,timeoutMs=2200) {
"""
helper="""    function lightsPurchaseClickTarget(element,root) {
      if (!element || !root) return element || null;

      const usable=(node)=>{
        if (!node || node===lightsAutoToggle || node.disabled || node.getAttribute?.('aria-disabled')==='true' || !visible(node)) return false;
        if (node.matches?.('button,[role="button"],a,[onclick]')) return true;
        try { return getComputedStyle(node).cursor==='pointer'; } catch (_) { return false; }
      };

      let node=element;
      for (let depth=0;node && depth<8;depth++,node=node.parentElement) {
        if (!root.contains(node) && node!==root) break;
        if (usable(node)) return node;
        if (node===root) break;
      }

      const rect=element.getBoundingClientRect?.();
      if (rect && rect.width>0 && rect.height>0) {
        const x=Math.max(1,Math.min(window.innerWidth-1,rect.left+rect.width/2));
        const y=Math.max(1,Math.min(window.innerHeight-1,rect.top+rect.height/2));
        const stack=document.elementsFromPoint?.(x,y) || [];
        for (const hit of stack) {
          if (!hit || (!root.contains(hit) && hit!==root)) continue;
          let current=hit;
          for (let depth=0;current && depth<8;depth++,current=current.parentElement) {
            if (!root.contains(current) && current!==root) break;
            if (usable(current)) return current;
            if (current===root) break;
          }
        }
      }

      return element;
    }

    async function tryLightsPurchaseAction(action,purchaseModal,before,runId,slot,mode) {
      if (runId!==lightsAutoRunId || !lightsAutoEnabled() || typeof action!=='function') return null;

      let fired=false;
      try { fired=action()!==false; } catch (_) { fired=false; }
      if (!fired) return null;

      recordDiagnostic('lights-purchase-attempt',{
        revision:HK_LIGHTS_CONFIRM_VERIFIED_REV,
        slot,
        mode
      });

      const probe=await waitLightsAcknowledge(runId,before,1500);
      if (probe.button || probe.changed) return probe;

      const current=lightsModalRoot();
      if (!current || current!==purchaseModal) {
        return {button:lightsAcknowledgeButton(current),changed:lightsBoardSignature()!==before};
      }
      return null;
    }

"""
if s.count(anchor)!=1:
    raise SystemExit("waitLightsPurchaseButton anchor missing")
s=s.replace(anchor,helper+anchor,1)

old="""      const purchaseButton=await waitLightsPurchaseButton(purchaseModal,runId);
      let confirmed=false;

      if (purchaseButton) {
        confirmed=dispatchAutoMapTap(purchaseButton,'lights-confirm-cost-'+slot);
      }

      if (!confirmed) {
        confirmed=tapLightsPurchaseFallback(purchaseModal,slot);
      }

      if (!confirmed) return {ok:false,reason:'purchase-tap-failed'};

      recordDiagnostic('lights-purchase-confirmed',{
        revision:HK_LIGHTS_CONFIRM_RECOVERY_REV,
        slot,
        selector:purchaseButton?'element':'coordinate-fallback'
      });

      const acknowledgement=await waitLightsAcknowledge(runId,before);
"""
new="""      const purchaseButton=await waitLightsPurchaseButton(purchaseModal,runId);
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
rep(old,new,"verified lights purchase")

rep("      lightsConfirmRecoveryRevision:HK_LIGHTS_CONFIRM_RECOVERY_REV,\n      start,",
    "      lightsConfirmRecoveryRevision:HK_LIGHTS_CONFIRM_RECOVERY_REV,\n      lightsConfirmVerifiedRevision:HK_LIGHTS_CONFIRM_VERIFIED_REV,\n      start,",
    "export revision")

for marker in [
    "// @version      1.18.32",
    "const BUILD_VERSION = '1.18.32';",
    "lights-confirm-verified-20260927-r2",
    "function lightsPurchaseClickTarget",
    "async function tryLightsPurchaseAction",
    "purchase-not-accepted",
    "lights-confirm-center-",
    "mode:confirmMode",
    "lights-confirm-recovery-20260927-r1",
    "fishing-zero-cast-exit-20260927-r1",
    "minigame-single-tap-20260927-r1",
    "treasure-final-reward-handoff-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("LIGHTS_CONFIRM_VERIFIED_1_18_32=PASS")
