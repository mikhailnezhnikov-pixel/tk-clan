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

rep("// @version      1.18.47",
    "// @version      1.18.48\n// @release-note Лабиринт: исправлено зависание Автокарты на уже открытом окне «Включенная/Выключенная лампочка». Детектор ламп теперь предпочитает внешний центральный диалог целиком (включая X и кнопку 1), а очистка старой модалки перед следующим ходом умеет закрывать внешний контейнер и его правый верхний угол без повторной траты ягоды. Добавлен отдельный regression contract для запуска/возобновления Автокарты с открытой модалкой лампы.",
    "version")
rep("const BUILD_VERSION = '1.18.47';",
    "const BUILD_VERSION = '1.18.48';",
    "build")
rep("  const HK_TREASURE_AUTOMAP_OWNERSHIP_REV='treasure-automap-module-ownership-20260927-r1';",
    "  const HK_TREASURE_AUTOMAP_OWNERSHIP_REV='treasure-automap-module-ownership-20260927-r1';\n  const HK_TREASURE_LIGHTS_RESUME_REV='treasure-lights-resume-open-modal-20260927-r1';",
    "revision")

old_root="""    function lightsModalRoot() {
      const rows=[];
"""
new_root="""    function lightsModalRoot() {
      // A lamp dialog is composed from several nested panels. The historical
      // scorer could pick the inner black content panel, which contains the
      // text/cost but not the top-right close control. When AutoMap resumed
      // with that modal already open, stale-modal cleanup could never dismiss
      // it and remained forever on "мини-игра". Prefer the real centered outer
      // action dialog first.
      const centered=treasureCenteredModalRoot();
      if (centered) {
        const centeredText=lightsModalText(centered);
        if (/лампоч|light\s*bulb|bulb|lights?\s*out/.test(centeredText)) {
          return centered;
        }
      }

      const rows=[];
"""
rep(old_root,new_root,"prefer outer lights modal")

old_stale="""    async function clearStaleLightsModalBeforeStep(runId,slot,timeoutMs=2200) {
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
new_stale="""    async function clearStaleLightsModalBeforeStep(runId,slot,timeoutMs=2600) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
        if (runId!==lightsAutoRunId || !lightsAutoEnabled()) return false;
        const root=lightsModalRoot();
        if (!root) return true;

        const ack=lightsAcknowledgeButton(root);
        if (ack && dispatchBattleTap(ack,'lights-clear-stale-ack-'+slot)) {
          recordDiagnostic('lights-stale-modal-cleared',{
            revision:HK_TREASURE_LIGHTS_RESUME_REV,
            slot,
            method:'ack'
          });
          await new Promise(resolve=>setTimeout(resolve,240));
          continue;
        }

        const close=lightsModalCloseButton(root);
        if (close && dispatchBattleTap(close,'lights-clear-stale-close-'+slot)) {
          recordDiagnostic('lights-stale-modal-cleared',{
            revision:HK_TREASURE_LIGHTS_RESUME_REV,
            slot,
            method:'close'
          });
          await new Promise(resolve=>setTimeout(resolve,240));
          continue;
        }

        // If the scored lamp root is still an inner panel, escalate to the
        // actual centered outer dialog. Important: stale cleanup NEVER presses
        // the cost button; it only dismisses the old modal, then the solver
        // recalculates and opens the correct next lamp.
        const outer=treasureCenteredModalRoot();
        if (outer) {
          const outerText=lightsModalText(outer);
          if (/лампоч|light\s*bulb|bulb|lights?\s*out/.test(outerText)) {
            const outerClose=
              lightsModalCloseButton(outer) ||
              autoMapModalCloseButton(outer);
            if (outerClose && dispatchBattleTap(outerClose,'lights-clear-stale-outer-close-'+slot)) {
              recordDiagnostic('lights-stale-modal-cleared',{
                revision:HK_TREASURE_LIGHTS_RESUME_REV,
                slot,
                method:'outer-close'
              });
              await new Promise(resolve=>setTimeout(resolve,260));
              continue;
            }

            const orr=outer.getBoundingClientRect?.();
            if (orr && orr.width>180 && orr.height>180) {
              if (dispatchBattleTapAt(
                orr.left+orr.width-20,
                orr.top+20,
                'lights-clear-stale-outer-corner-'+slot
              )) {
                recordDiagnostic('lights-stale-modal-cleared',{
                  revision:HK_TREASURE_LIGHTS_RESUME_REV,
                  slot,
                  method:'outer-corner'
                });
                await new Promise(resolve=>setTimeout(resolve,300));
                continue;
              }
            }
          }
        }

        const rr=root.getBoundingClientRect?.();
        if (rr && rr.width>120 && rr.height>120) {
          if (dispatchBattleTapAt(rr.left+rr.width-18,rr.top+18,'lights-clear-stale-corner-'+slot)) {
            recordDiagnostic('lights-stale-modal-cleared',{
              revision:HK_TREASURE_LIGHTS_RESUME_REV,
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
rep(old_stale,new_stale,"robust stale lights modal drain")

rep("      treasureAutoMapOwnershipRevision:HK_TREASURE_AUTOMAP_OWNERSHIP_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "      treasureAutoMapOwnershipRevision:HK_TREASURE_AUTOMAP_OWNERSHIP_REV,\n      treasureLightsResumeRevision:HK_TREASURE_LIGHTS_RESUME_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "export lights resume revision")

for marker in [
    "// @version      1.18.48",
    "const BUILD_VERSION = '1.18.48';",
    "treasure-lights-resume-open-modal-20260927-r1",
    "const centered=treasureCenteredModalRoot();",
    "const centeredText=lightsModalText(centered);",
    "lights-clear-stale-outer-close",
    "lights-clear-stale-outer-corner",
    "treasure-automap-module-ownership-20260927-r1",
    "treasure-location-modal-root-20260927-r1",
    "treasure-chest-map-foreground-guard-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_LIGHTS_RESUME_OPEN_MODAL_1_18_48=PASS")
