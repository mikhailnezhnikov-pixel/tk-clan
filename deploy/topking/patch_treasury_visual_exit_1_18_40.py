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

rep("// @version      1.18.39",
    "// @version      1.18.40\n// @release-note Сокровищница: завершение теперь определяется и по фактическому экрану — заголовок «Сокровищница» + видимое «Активировано» + кнопка «Покинуть локацию». После этого Автокарта больше не трогает сундук и выполняет отдельный одноразовый клик по нижней кнопке выхода, ждёт реального возврата на Карту Сокровищ и только затем продолжает маршрут.",
    "version")
rep("const BUILD_VERSION = '1.18.39';",
    "const BUILD_VERSION = '1.18.40';",
    "build")
rep("  const HK_TREASURY_EXIT_AFTER_CLAIM_REV = 'treasury-exit-after-claim-20260927-r1';",
    "  const HK_TREASURY_EXIT_AFTER_CLAIM_REV = 'treasury-exit-after-claim-20260927-r1';\n  const HK_TREASURY_VISUAL_EXIT_REV = 'treasury-visual-exit-20260927-r2';",
    "revision")

anchor="""    function autoMapTreasuryCompleted() {
      return autoMapTreasuryChestRows().some(row=>row.activated);
    }
"""
insert="""    function autoMapTreasuryScreenVisible() {
      const headings=[...document.querySelectorAll('h1,h2,h3,[role="heading"],header,div,span')]
        .filter(visible)
        .map(element=>clean(element.innerText||element.textContent||'').trim())
        .filter(text=>text && text.length<=80);
      return headings.some(text=>/^(?:Сокровищница|Treasury)$/i.test(text));
    }

    function autoMapTreasuryActivatedMarker() {
      return [...document.querySelectorAll('div,span,p,strong,b')]
        .filter(visible)
        .map(element=>({
          element,
          text:clean(element.innerText||element.textContent||'').trim(),
          rect:element.getBoundingClientRect?.()
        }))
        .filter(row=>/^(?:Активировано|Activated|Получено|Claimed)$/i.test(row.text))
        .filter(row=>row.rect && row.rect.width>20 && row.rect.height>10)
        .sort((a,b)=>a.rect.width*a.rect.height-b.rect.width*b.rect.height)[0]?.element || null;
    }

    function autoMapTreasuryCompletedVisual() {
      return !!(
        autoMapTreasuryScreenVisible() &&
        autoMapTreasuryActivatedMarker() &&
        autoMapExitButton()
      );
    }

    function autoMapTreasuryDone() {
      return autoMapTreasuryCompleted() || autoMapTreasuryCompletedVisual();
    }

    async function autoMapDirectTreasuryExit() {
      if (!autoMapEnabled() || !autoMapTreasuryDone()) return false;
      const exit=autoMapExitButton();
      if (!exit) return false;

      await autoMapWaitActionGap();
      if (!autoMapEnabled() || !autoMapTreasuryDone()) return false;

      const runId=autoMapRunId;
      const before=autoMapStateFingerprint();
      const rect=exit.getBoundingClientRect?.();
      autoMapActionCount+=1;
      autoMapLastActionAt=Date.now();
      autoMapStatus('treasury выход',{
        revision:HK_TREASURY_VISUAL_EXIT_REV
      });

      recordDiagnostic('treasury-exit-target',{
        revision:HK_TREASURY_VISUAL_EXIT_REV,
        text:clean(exit.innerText||exit.textContent||'').trim(),
        left:Math.round(rect?.left||0),
        top:Math.round(rect?.top||0),
        width:Math.round(rect?.width||0),
        height:Math.round(rect?.height||0)
      });

      if (!dispatchAutoMapTap(exit,'treasury-leave-location-direct')) {
        autoMapStatus('treasury клик не прошёл',{
          revision:HK_TREASURY_VISUAL_EXIT_REV
        });
        return false;
      }

      // Direct exit usually changes the room immediately. If the game places a
      // confirmation modal in front, confirm only that modal once; never click
      // the claimed chest again.
      const started=Date.now();
      let modalConfirmed=false;
      while (Date.now()-started<4200) {
        if (runId!==autoMapRunId || !autoMapEnabled()) return false;

        if (treasureGuideScreenVisible() && !autoMapTreasuryScreenVisible()) {
          autoMapRetryNotBefore=0;
          autoMapCurrentLot='';
          lastSignature='';
          autoMapReturnNotBefore=Date.now()+300;
          recordDiagnostic('treasury-exit-after-claim',{
            revision:HK_TREASURY_VISUAL_EXIT_REV,
            result:'map-visible'
          });
          setTimeout(()=>void runAutoMapTick('treasury-direct-exit-complete'),380);
          return true;
        }

        if (autoMapStateFingerprint()!==before && !autoMapTreasuryScreenVisible()) {
          autoMapRetryNotBefore=0;
          autoMapCurrentLot='';
          lastSignature='';
          recordDiagnostic('treasury-exit-after-claim',{
            revision:HK_TREASURY_VISUAL_EXIT_REV,
            result:'screen-changed'
          });
          setTimeout(()=>void runAutoMapTick('treasury-direct-exit-changed'),380);
          return true;
        }

        if (!modalConfirmed) {
          const modal=treasureModalRoot(null);
          if (modal) {
            const action=autoMapModalPrimaryButton(modal,null);
            if (action) {
              modalConfirmed=dispatchAutoMapTap(action,'treasury-leave-confirm-direct');
              if (modalConfirmed) {
                autoMapLastActionAt=Date.now();
                recordDiagnostic('treasury-exit-confirm',{
                  revision:HK_TREASURY_VISUAL_EXIT_REV
                });
              }
            }
          }
        }

        await new Promise(resolve=>setTimeout(resolve,90));
      }

      autoMapRetryNotBefore=Date.now()+900;
      autoMapStatus('treasury жду карту',{
        revision:HK_TREASURY_VISUAL_EXIT_REV
      });
      return false;
    }

"""
if s.count(anchor)!=1:
    raise SystemExit("treasury completed anchor missing")
s=s.replace(anchor,anchor+"\n"+insert,1)

# Early completed-treasury recovery must happen before the generic pause gate.
old_gate="""      ensureAutoMapToggle();

      if (Date.now()<autoMapRetryNotBefore) {
        autoMapStatus('пауза');
        return false;
      }

      // After the central reward is visibly Activated, the lights runner has no
"""
new_gate="""      ensureAutoMapToggle();

      // A completed Treasury is a navigation handoff, not another chest
      // purchase. Detect it from the visible screen even if the claimed chest's
      // lot-id changed after activation. During a previous retry cooldown we do
      // not re-buy anything; we simply wait and then perform the exit.
      if (autoMapTreasuryDone()) {
        if (Date.now()<autoMapRetryNotBefore) {
          const waitMs=autoMapRetryNotBefore-Date.now();
          autoMapStatus('пауза → выход',{
            revision:HK_TREASURY_VISUAL_EXIT_REV,
            waitMs
          });
          setTimeout(()=>void runAutoMapTick('treasury-exit-after-pause'),Math.min(waitMs+80,2200));
          return false;
        }
        autoMapRunning=true;
        const treasuryRunId=autoMapRunId;
        try {
          return await autoMapDirectTreasuryExit();
        } finally {
          if (treasuryRunId===autoMapRunId) autoMapRunning=false;
        }
      }

      if (Date.now()<autoMapRetryNotBefore) {
        autoMapStatus('пауза');
        return false;
      }

      // After the central reward is visibly Activated, the lights runner has no
"""
rep(old_gate,new_gate,"early treasury exit before pause")

# Use unified done predicate in normal room branch too.
rep("        if (autoMapTreasuryCompleted()) {",
    "        if (autoMapTreasuryDone()) {",
    "normal treasury completed branch")

# In normal branch use the direct exit helper, not generic purchase flow.
old_normal="""          const exit=autoMapExitButton();
          if (exit) {
            autoMapStatus('treasury выход',{
              revision:HK_TREASURY_EXIT_AFTER_CLAIM_REV
            });
            const left=await autoMapTapAndConfirm(exit,'treasury-leave-location',null);
            if (left) {
              autoMapCurrentLot='';
              lastSignature='';
              autoMapReturnNotBefore=Date.now()+350;
              recordDiagnostic('treasury-exit-after-claim',{
                revision:HK_TREASURY_EXIT_AFTER_CLAIM_REV,
                result:'clicked'
              });
              setTimeout(()=>void runAutoMapTick('treasury-left-location'),420);
            }
            return left;
          }

          autoMapStatus('treasury жду выход',{
            revision:HK_TREASURY_EXIT_AFTER_CLAIM_REV
          });
          return false;
"""
new_normal="""          return await autoMapDirectTreasuryExit();
"""
rep(old_normal,new_normal,"normal direct treasury exit")

rep("      treasuryExitAfterClaimRevision:HK_TREASURY_EXIT_AFTER_CLAIM_REV,\n      start,",
    "      treasuryExitAfterClaimRevision:HK_TREASURY_EXIT_AFTER_CLAIM_REV,\n      treasuryVisualExitRevision:HK_TREASURY_VISUAL_EXIT_REV,\n      start,",
    "export visual treasury revision")

for marker in [
    "// @version      1.18.40",
    "const BUILD_VERSION = '1.18.40';",
    "treasury-visual-exit-20260927-r2",
    "function autoMapTreasuryScreenVisible()",
    "function autoMapTreasuryActivatedMarker()",
    "function autoMapTreasuryCompletedVisual()",
    "function autoMapTreasuryDone()",
    "async function autoMapDirectTreasuryExit()",
    "treasury-leave-location-direct",
    "пауза → выход",
    "treasury-direct-exit-complete",
    "treasury-exit-after-claim-20260927-r1",
    "lights-fast-confirm-20260927-r1",
    "trader-keys-fast-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURY_VISUAL_EXIT_1_18_40=PASS")
