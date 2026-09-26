from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def r(a,b,label):
    global s
    n=s.count(a)
    if n!=1: raise SystemExit(f"{label}: expected 1 got {n}")
    s=s.replace(a,b,1)

r("// @version      1.18.19",
  "// @version      1.18.20\n// @release-note Автокарта: кнопка «Начать новое путешествие» больше не считается признаком конца карты. Активные клетки имеют абсолютный приоритет; пока есть mf_treasurelot_active_sl*, сброс карты запрещён. Случайно открытое окно сброса закрывается через «Назад». Завершение фиксируется только после устойчивого отсутствия активных клеток.",
  "version")
r("const BUILD_VERSION = '1.18.19';","const BUILD_VERSION = '1.18.20';","build")
r("  const HK_TREASURE_AUTO_MAP_START_LOCK_REV='treasure-auto-map-start-lock-20260926-r4';",
  "  const HK_TREASURE_AUTO_MAP_START_LOCK_REV='treasure-auto-map-start-lock-20260926-r4';\n  const HK_TREASURE_AUTO_MAP_ACTIVE_PRIORITY_REV='treasure-auto-map-active-priority-20260926-r5';",
  "revision")

r("    const AUTO_MAP_START_LOCK_MS=9000;\n    const AUTO_MAP_LOOP_MS=420;",
  "    const AUTO_MAP_START_LOCK_MS=9000;\n    const AUTO_MAP_NO_ACTIVE_COMPLETE_MS=4500;\n    const AUTO_MAP_LOOP_MS=420;",
  "complete wait")

r("    let autoMapLastStatus='';",
  "    let autoMapLastStatus='';\n    let autoMapNoActiveSince=0;",
  "no active state")

anchor="    function autoMapJourneyButton() {"
if s.count(anchor)!=1: raise SystemExit("journey anchor")
helper="""    function autoMapAbandonModalRoot() {
      const nodes=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"]')].filter(visible);
      for (const node of nodes) {
        const text=clean(node.innerText||node.textContent||'');
        if (/завершит текущ(?:ее|ий) путешествие|будет начата новая карта|нельзя будет вернуться/i.test(text)) {
          return node;
        }
      }
      return null;
    }

    function autoMapAbandonBackButton(root) {
      if (!root) return null;
      return [...root.querySelectorAll('button,[role="button"],a,div,span')]
        .filter(el=>el && el!==autoMapToggle && !el.disabled && visible(el))
        .map(el=>({el,text:clean(el.innerText||el.textContent||'').trim(),area:(el.getBoundingClientRect?.().width||0)*(el.getBoundingClientRect?.().height||0)}))
        .filter(row=>/^(?:Назад|Back)$/i.test(row.text))
        .sort((a,b)=>a.area-b.area)[0]?.el || null;
    }

    async function autoMapDismissAbandonModalIfNeeded() {
      const root=autoMapAbandonModalRoot();
      if (!root) return false;
      const activeCount=autoMapMapCards().length;
      if (!autoMapSessionStarted() && activeCount===0) return false;
      const back=autoMapAbandonBackButton(root);
      if (!back) {
        autoMapStatus('закрой сброс');
        return false;
      }
      autoMapStatus('закрываю сброс',{activeCount});
      autoMapLastActionAt=Date.now();
      dispatchAutoMapTap(back,'abandon-back');
      setAutoMapStartLock(0);
      await new Promise(resolve=>setTimeout(resolve,450));
      return true;
    }

"""
s=s.replace(anchor,helper+anchor,1)

old="""        // The same game button is present both before the first map and after the
        // completed map. Persist session state so reloads cannot start a second map.
        if (treasureGuideScreenVisible() && autoMapJourneyButton()) {
          if (!autoMapSessionStarted()) {
            const lockAt=autoMapStartLockAt();
            if (lockAt && Date.now()-lockAt<AUTO_MAP_START_LOCK_MS) {
              autoMapStatus('жду открытия',{elapsedMs:Date.now()-lockAt});
              return false;
            }
            if (lockAt) setAutoMapStartLock(0);
            const journey=autoMapJourneyButton();
            setAutoMapStartLock(Date.now());
            autoMapStatus('старт карты');
            const started=await autoMapTapAndConfirm(journey,'new-journey',1);
            if (started && autoMapMapCards().length>0) {
              setAutoMapSessionStarted(true);
              setAutoMapStartLock(0);
              autoMapStatus('карта открыта');
            } else {
              autoMapStatus('жду открытия');
            }
            return started;
          }

          setAutoMapStartLock(0);
          autoMapStatus('ГОТОВО');
          recordDiagnostic('treasure-auto-map-complete',{
            revision:HK_TREASURE_AUTO_MAP_START_LOCK_REV,
            actions:autoMapActionCount,
            source
          });
          setAutoMapEnabled(false,{reason:'map-complete',preserveStatus:'ГОТОВО'});
          return true;
        }

        // Normal map traversal: lowest currently active slot first, then rescan.
        if (treasureGuideScreenVisible()) {
          const target=autoMapMapCards()[0];
          if (target) {
            if (!autoMapSessionStarted()) setAutoMapSessionStarted(true);
            setAutoMapStartLock(0);
            autoMapCurrentLot=target.lotId;
            autoMapStatus('ячейка '+String(target.slot),{
              lotId:target.lotId,
              cost:target.cost
            });
            const ok=await autoMapTapAndConfirm(target.element,'map-'+target.lotId,target.cost);
            if (ok) {
              autoMapCurrentLot='';
              lastSignature='';
              setTimeout(checkPuzzle,100);
            }
            return ok;
          }
          autoMapStatus('жду карту');
          return false;
        }
"""
new="""        // A reset/new-journey warning may be visible over a still-active map.
        // If the current journey has active cells, close that warning first.
        if (await autoMapDismissAbandonModalIfNeeded()) {
          autoMapNoActiveSince=0;
          return true;
        }

        // Current-map cells have absolute priority over the persistent
        // "Начать новое путешествие" reset button.
        if (treasureGuideScreenVisible()) {
          const target=autoMapMapCards()[0];
          if (target) {
            autoMapNoActiveSince=0;
            if (!autoMapSessionStarted()) setAutoMapSessionStarted(true);
            setAutoMapStartLock(0);
            autoMapCurrentLot=target.lotId;
            autoMapStatus('ячейка '+String(target.slot),{
              lotId:target.lotId,
              cost:target.cost
            });
            const ok=await autoMapTapAndConfirm(target.element,'map-'+target.lotId,target.cost);
            if (ok) {
              autoMapCurrentLot='';
              lastSignature='';
              setTimeout(checkPuzzle,100);
            }
            return ok;
          }

          const journey=autoMapJourneyButton();
          if (journey) {
            if (!autoMapSessionStarted()) {
              autoMapNoActiveSince=0;
              const lockAt=autoMapStartLockAt();
              if (lockAt && Date.now()-lockAt<AUTO_MAP_START_LOCK_MS) {
                autoMapStatus('жду открытия',{elapsedMs:Date.now()-lockAt});
                return false;
              }
              if (lockAt) setAutoMapStartLock(0);
              setAutoMapStartLock(Date.now());
              autoMapStatus('старт карты');
              const started=await autoMapTapAndConfirm(journey,'new-journey',1);
              if (started && autoMapMapCards().length>0) {
                setAutoMapSessionStarted(true);
                setAutoMapStartLock(0);
                autoMapStatus('карта открыта');
              } else {
                autoMapStatus('жду открытия');
              }
              return started;
            }

            // During an active journey this button is always present as a RESET.
            // Only stable absence of all active cells may mean completion.
            if (!autoMapNoActiveSince) autoMapNoActiveSince=Date.now();
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
          }

          autoMapNoActiveSince=0;
          autoMapStatus('жду карту');
          return false;
        }
"""
r(old,new,"reorder map priority")

r("""          const alreadyInside=!autoMapJourneyButton();
          setAutoMapSessionStarted(alreadyInside);
""",
  """          const alreadyInside=autoMapMapCards().length>0 || !autoMapJourneyButton();
          setAutoMapSessionStarted(alreadyInside);
""",
  "enable inference")

r("      autoMapCurrentLot='';\n      if (!value) autoMapSkipLotsUntil.clear();",
  "      autoMapCurrentLot='';\n      autoMapNoActiveSince=0;\n      if (!value) autoMapSkipLotsUntil.clear();",
  "clear empty timer")

r("      treasureAutoMapStartLockRevision:HK_TREASURE_AUTO_MAP_START_LOCK_REV,\n      start,",
  "      treasureAutoMapStartLockRevision:HK_TREASURE_AUTO_MAP_START_LOCK_REV,\n      treasureAutoMapActivePriorityRevision:HK_TREASURE_AUTO_MAP_ACTIVE_PRIORITY_REV,\n      start,",
  "export revision")

for x in [
  "// @version      1.18.20",
  "const BUILD_VERSION = '1.18.20';",
  "treasure-auto-map-active-priority-20260926-r5",
  "AUTO_MAP_NO_ACTIVE_COMPLETE_MS=4500",
  "autoMapDismissAbandonModalIfNeeded",
  "autoMapMapCards().length>0 || !autoMapJourneyButton()",
  "emptyFor<AUTO_MAP_NO_ACTIVE_COMPLETE_MS",
  "treasure-auto-map-start-lock-20260926-r4"
]:
    if x not in s: raise SystemExit("missing "+x)

p.write_text(s,encoding="utf-8")
print("TREASURE_AUTO_MAP_ACTIVE_PRIORITY_1_18_20=PASS")
