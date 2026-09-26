from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def rep(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f"{label}: expected 1 got {n}")
    s=s.replace(old,new,1)

rep("// @version      1.18.19",
    "// @version      1.18.20\n// @release-note Автокарта: активные клетки текущей Карты Сокровищ теперь имеют абсолютный приоритет над кнопкой сброса «Начать новое путешествие». Окно сброса закрывается через «Назад». Завершение карты требует устойчивого отсутствия активных клеток.",
    "version")
rep("const BUILD_VERSION = '1.18.19';",
    "const BUILD_VERSION = '1.18.20';",
    "build")
rep("  const HK_TREASURE_AUTO_MAP_START_LOCK_REV='treasure-auto-map-start-lock-20260926-r4';",
    "  const HK_TREASURE_AUTO_MAP_START_LOCK_REV='treasure-auto-map-start-lock-20260926-r4';\n  const HK_TREASURE_AUTO_MAP_ACTIVE_PRIORITY_REV='treasure-auto-map-active-priority-20260926-r5';",
    "revision")
rep("    const AUTO_MAP_START_LOCK_MS=9000;\n    const AUTO_MAP_LOOP_MS=420;",
    "    const AUTO_MAP_START_LOCK_MS=9000;\n    const AUTO_MAP_NO_ACTIVE_COMPLETE_MS=4500;\n    const AUTO_MAP_LOOP_MS=420;",
    "complete-wait")
rep("    let autoMapLastStatus='';",
    "    let autoMapLastStatus='';\n    let autoMapNoActiveSince=0;",
    "empty-timer")

journey_anchor="    function autoMapJourneyButton() {"
if s.count(journey_anchor)!=1:
    raise SystemExit("journey anchor missing")
helpers="""    function autoMapActiveCellCount() {
      return [...document.querySelectorAll('[data-lot-id^="mf_treasurelot_active_sl"]')]
        .filter(visible).length;
    }

    function autoMapAbandonModalRoot() {
      const nodes=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"]')].filter(visible);
      for (const node of nodes) {
        const text=clean(node.innerText||node.textContent||'');
        if (/завершит текущее путешествие|будет начата новая карта|нельзя будет вернуться/i.test(text)) return node;
      }
      return null;
    }

    function autoMapAbandonBackButton(root) {
      if (!root) return null;
      return [...root.querySelectorAll('button,[role="button"],a,div,span')]
        .filter(el=>el && el!==autoMapToggle && !el.disabled && visible(el))
        .map(el=>({el,text:clean(el.innerText||el.textContent||'').trim()}))
        .find(row=>/^(?:Назад|Back)$/i.test(row.text))?.el || null;
    }

"""
s=s.replace(journey_anchor,helpers+journey_anchor,1)

tick_anchor="""        // The same game button is present both before the first map and after the
        // completed map. Persist session state so reloads cannot start a second map.
"""
if s.count(tick_anchor)!=1:
    raise SystemExit("tick anchor missing")
guard="""        // Active cells always mean the current journey is still alive.
        // Handle them before even looking at the persistent reset button.
        if (treasureGuideScreenVisible()) {
          const activeCount=autoMapActiveCellCount();
          if (activeCount>0) {
            autoMapNoActiveSince=0;
            if (!autoMapSessionStarted()) setAutoMapSessionStarted(true);
            setAutoMapStartLock(0);

            const abandonRoot=autoMapAbandonModalRoot();
            if (abandonRoot) {
              const back=autoMapAbandonBackButton(abandonRoot);
              if (back) {
                autoMapStatus('закрываю сброс',{activeCount});
                dispatchAutoMapTap(back,'abandon-back');
                await new Promise(resolve=>setTimeout(resolve,450));
                return true;
              }
              autoMapStatus('закрой сброс',{activeCount});
              return false;
            }

            const target=autoMapMapCards()[0];
            if (!target) {
              // Active cells may be temporarily skipped after 409; that is not completion.
              autoMapStatus('жду ячейку',{activeCount});
              return false;
            }

            autoMapCurrentLot=target.lotId;
            autoMapStatus('ячейка '+String(target.slot),{
              lotId:target.lotId,
              cost:target.cost,
              activeCount
            });
            const ok=await autoMapTapAndConfirm(target.element,'map-'+target.lotId,target.cost);
            if (ok) {
              autoMapCurrentLot='';
              lastSignature='';
              setTimeout(checkPuzzle,100);
            }
            return ok;
          }
        }

"""
s=s.replace(tick_anchor,guard+tick_anchor,1)

rep("""          setAutoMapStartLock(0);
          autoMapStatus('ГОТОВО');
          recordDiagnostic('treasure-auto-map-complete',{
            revision:HK_TREASURE_AUTO_MAP_SESSION_REV,
            actions:autoMapActionCount,
            source
          });
          setAutoMapEnabled(false,{reason:'map-complete',preserveStatus:'ГОТОВО'});
          return true;
""",
"""          if (!autoMapNoActiveSince) autoMapNoActiveSince=Date.now();
          const emptyFor=Date.now()-autoMapNoActiveSince;
          if (emptyFor<AUTO_MAP_NO_ACTIVE_COMPLETE_MS) {
            autoMapStatus('проверяю карту',{emptyForMs:emptyFor});
            return false;
          }

          setAutoMapStartLock(0);
          autoMapStatus('ГОТОВО');
          recordDiagnostic('treasure-auto-map-complete',{
            revision:HK_TREASURE_AUTO_MAP_ACTIVE_PRIORITY_REV,
            actions:autoMapActionCount,
            source,
            emptyForMs:emptyFor
          });
          setAutoMapEnabled(false,{reason:'map-complete',preserveStatus:'ГОТОВО'});
          return true;
""",
"stable completion")

rep("          const alreadyInside=!autoMapJourneyButton();",
    "          const alreadyInside=autoMapActiveCellCount()>0 || !autoMapJourneyButton();",
    "enable inference")

rep("      autoMapCurrentLot='';\n      if (!value) autoMapSkipLotsUntil.clear();",
    "      autoMapCurrentLot='';\n      autoMapNoActiveSince=0;\n      if (!value) autoMapSkipLotsUntil.clear();",
    "timer reset")

rep("      treasureAutoMapStartLockRevision:HK_TREASURE_AUTO_MAP_START_LOCK_REV,\n      start,",
    "      treasureAutoMapStartLockRevision:HK_TREASURE_AUTO_MAP_START_LOCK_REV,\n      treasureAutoMapActivePriorityRevision:HK_TREASURE_AUTO_MAP_ACTIVE_PRIORITY_REV,\n      start,",
    "export")

for marker in [
    "// @version      1.18.20",
    "const BUILD_VERSION = '1.18.20';",
    "treasure-auto-map-active-priority-20260926-r5",
    "AUTO_MAP_NO_ACTIVE_COMPLETE_MS=4500",
    "function autoMapActiveCellCount()",
    "dispatchAutoMapTap(back,'abandon-back')",
    "autoMapActiveCellCount()>0 || !autoMapJourneyButton()",
    "emptyFor<AUTO_MAP_NO_ACTIVE_COMPLETE_MS",
    "treasure-auto-map-start-lock-20260926-r4"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_AUTO_MAP_ACTIVE_PRIORITY_1_18_20=PASS")
