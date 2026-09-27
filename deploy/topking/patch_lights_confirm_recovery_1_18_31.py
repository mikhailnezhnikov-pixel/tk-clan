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

rep("// @version      1.18.30",
    "// @version      1.18.31\n// @release-note Лампочки: подтверждение покупки восстановлено. После появления модалки скрипт отдельно ждёт готовность кнопки стоимости 1, умеет продолжить уже из открытого окна и использует безопасный fallback по нижней центральной кнопке. При включённой Автокарте временная ошибка подтверждения больше не выключает Автолампы навсегда.",
    "version")
rep("const BUILD_VERSION = '1.18.30';",
    "const BUILD_VERSION = '1.18.31';",
    "build")
rep("  const HK_FISHING_ZERO_CAST_EXIT_REV='fishing-zero-cast-exit-20260927-r1';",
    "  const HK_FISHING_ZERO_CAST_EXIT_REV='fishing-zero-cast-exit-20260927-r1';\n  const HK_LIGHTS_CONFIRM_RECOVERY_REV='lights-confirm-recovery-20260927-r1';",
    "revision")

old_button="""    function lightsPurchaseButton(root) {
      if (!root) return null;
      const rr=root.getBoundingClientRect?.();
      if (!rr) return null;
      const candidates=[...root.querySelectorAll('button,[role="button"],a')]
        .filter(element=>element && element!==lightsAutoToggle && !element.disabled && visible(element))
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          let score=0;
          if (text==='1') score+=220;
          if (/^(?:понятно|got it|understood|ok|okay)$/i.test(text)) score-=300;
          if (/закрыть|close|×|✕|назад|back/i.test(text)) score-=300;
          if (rect.width>=rr.width*0.28) score+=35;
          if (rect.height>=38) score+=25;
          if (rect.top>=rr.top+rr.height*0.55) score+=35;
          return {element,score};
        })
        .filter(row=>row.score>=180)
        .sort((a,b)=>b.score-a.score);
      return candidates[0]?.element || null;
    }
"""
new_button="""    function lightsPurchaseButton(root) {
      if (!root) return null;
      const rr=root.getBoundingClientRect?.();
      if (!rr) return null;
      const candidates=[...root.querySelectorAll('button,[role="button"],a,div,span')]
        .filter(element=>
          element &&
          element!==lightsAutoToggle &&
          !element.disabled &&
          element.getAttribute?.('aria-disabled')!=='true' &&
          visible(element)
        )
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const rect=element.getBoundingClientRect?.() || {left:0,top:0,width:0,height:0};
          const style=getComputedStyle(element);
          const actionable=
            element.matches?.('button,[role="button"],a') ||
            !!element.onclick ||
            style.cursor==='pointer';
          let score=actionable?120:0;
          if (text==='1') score+=240;
          else if (/^(?:🫐|🍒|🍓)?\s*1$/u.test(text)) score+=190;
          if (/^(?:понятно|got it|understood|ok|okay)$/i.test(text)) score-=400;
          if (/закрыть|close|×|✕|назад|back/i.test(text)) score-=400;
          if (rect.width>=rr.width*0.28 && rect.width<=rr.width*0.92) score+=55;
          if (rect.height>=38 && rect.height<=150) score+=45;
          if (rect.top>=rr.top+rr.height*0.55) score+=55;
          const cx=rect.left+rect.width/2;
          const centerX=rr.left+rr.width/2;
          if (Math.abs(cx-centerX)<=rr.width*0.30) score+=45;
          return {element,score,rect,actionable};
        })
        .filter(row=>row.score>=220)
        .sort((a,b)=>b.score-a.score || b.rect.width*b.rect.height-a.rect.width*a.rect.height);

      if (candidates[0]?.element) return candidates[0].element;

      // Shared fallback supports clickable DIV/SPAN wrappers used by some layouts.
      try {
        return treasureActionButton(root,{id:'',quantity:1});
      } catch (_) {
        return null;
      }
    }

    async function waitLightsPurchaseButton(root,runId,timeoutMs=2200) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
        if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return null;
        const current=lightsModalRoot() || root;
        const button=lightsPurchaseButton(current);
        if (button) return button;
        await new Promise(resolve=>setTimeout(resolve,80));
      }
      return null;
    }

    function tapLightsPurchaseFallback(root,slot) {
      if (!root) return false;
      const rr=root.getBoundingClientRect?.();
      if (!rr) return false;
      return dispatchBattleTapAt(
        rr.left+rr.width/2,
        rr.top+rr.height*0.86,
        'lights-confirm-cost-fallback-'+slot
      );
    }
"""
rep(old_button,new_button,"lights purchase finder")

old_step="""    async function runLightsModalStep(before,target,slot,runId) {
      if (!target || !target.isConnected) return {ok:false,reason:'target-missing'};

      const opened=dispatchBattleTap(target,'lights-open-'+slot);
      if (!opened) return {ok:false,reason:'target-tap-failed'};

      const purchaseModal=await waitLightsModal(runId);
      if (!purchaseModal) return {ok:false,reason:'purchase-modal-missing'};

      const purchaseButton=lightsPurchaseButton(purchaseModal);
      if (!purchaseButton) return {ok:false,reason:'purchase-button-missing'};

      if (!dispatchBattleTap(purchaseButton,'lights-confirm-cost-'+slot)) {
        return {ok:false,reason:'purchase-tap-failed'};
      }

      const acknowledgement=await waitLightsAcknowledge(runId,before);
"""
new_step="""    async function runLightsModalStep(before,target,slot,runId) {
      if (!target || !target.isConnected) return {ok:false,reason:'target-missing'};

      // Recover an already-open purchase window first. This is important after a
      // transient selector/timing failure: do not tap the lamp a second time.
      let purchaseModal=lightsModalRoot();

      if (!purchaseModal) {
        const opened=dispatchAutoMapTap(target,'lights-open-'+slot);
        if (!opened) return {ok:false,reason:'target-tap-failed'};
        purchaseModal=await waitLightsModal(runId);
      }

      if (!purchaseModal) return {ok:false,reason:'purchase-modal-missing'};

      const purchaseButton=await waitLightsPurchaseButton(purchaseModal,runId);
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
rep(old_step,new_step,"lights modal recovery")

old_fail="""    function failLightsAuto(reason,data={}) {
      try { localStorage.setItem(LIGHTS_AUTO_STORAGE_KEY,'0'); } catch (_) {}
      lightsAutoRunId += 1;
      lightsAutoRunning=false;
      updateLightsAutoToggle();
      recordDiagnostic('lights-auto-stop',{revision:HK_LIGHTS_AUTO_REV,reason,...data});
      return false;
    }
"""
new_fail="""    function failLightsAuto(reason,data={}) {
      const autoMapOwnsLights=(()=>{
        try {
          return typeof autoMapEnabled==='function' &&
            autoMapEnabled() &&
            getSignature().startsWith('LIGHTS|');
        } catch (_) {
          return false;
        }
      })();

      lightsAutoRunId += 1;
      lightsAutoRunning=false;

      if (autoMapOwnsLights) {
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
      updateLightsAutoToggle();
      recordDiagnostic('lights-auto-stop',{revision:HK_LIGHTS_AUTO_REV,reason,...data});
      return false;
    }
"""
rep(old_fail,new_fail,"lights fail recovery")

rep("      fishingZeroCastExitRevision:HK_FISHING_ZERO_CAST_EXIT_REV,\n      start,",
    "      fishingZeroCastExitRevision:HK_FISHING_ZERO_CAST_EXIT_REV,\n      lightsConfirmRecoveryRevision:HK_LIGHTS_CONFIRM_RECOVERY_REV,\n      start,",
    "export revision")

for marker in [
    "// @version      1.18.31",
    "const BUILD_VERSION = '1.18.31';",
    "lights-confirm-recovery-20260927-r1",
    "async function waitLightsPurchaseButton",
    "tapLightsPurchaseFallback",
    "Recover an already-open purchase window first",
    "lights-purchase-confirmed",
    "lights-auto-recover",
    "dispatchAutoMapTap(purchaseButton,'lights-confirm-cost-'+slot)",
    "fishing-zero-cast-exit-20260927-r1",
    "fishing-human-fast-20260927-r1",
    "treasure-final-reward-handoff-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("LIGHTS_CONFIRM_RECOVERY_1_18_31=PASS")
