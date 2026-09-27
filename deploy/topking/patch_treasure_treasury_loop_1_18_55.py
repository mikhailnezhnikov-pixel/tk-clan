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

rep("// @version      1.18.54",
    "// @version      1.18.55\n// @release-note Сокровищница: левый путь теперь одноразовый на одно посещение — после входа в левую комнату остальные пути заблокированы до возврата на карту. После получения награды Автокарта выходит из локации и продолжает маршрут. Когда активных клеток больше нет, Автокарта не выключается, а автоматически начинает новую Карту сокровищ и продолжает цикл.",
    "version")
rep("const BUILD_VERSION = '1.18.54';",
    "const BUILD_VERSION = '1.18.55';",
    "build")
rep("  const HK_TREASURY_LEFT_PATH_REV = 'treasury-left-path-exit-recovery-20260927-r1';",
    "  const HK_TREASURY_LEFT_PATH_REV = 'treasury-left-path-exit-recovery-20260927-r1';\n  const HK_TREASURY_LOOP_REV = 'treasury-left-once-continuous-map-20260927-r1';",
    "revision")

rep("    const AUTO_MAP_START_LOCK_KEY='hk:treasure:auto-map-start-lock:v1';",
    "    const AUTO_MAP_START_LOCK_KEY='hk:treasure:auto-map-start-lock:v1';\n    const AUTO_MAP_TREASURY_LOCK_KEY='hk:treasure:auto-map-treasury-left:v1';",
    "treasury lock storage key")

anchor="""    function autoMapModulesRunning() {
"""
helper="""    function autoMapTreasuryLeftSelected() {
      try{return localStorage.getItem(AUTO_MAP_TREASURY_LOCK_KEY)==='1';}
      catch(_){return false;}
    }

    function setAutoMapTreasuryLeftSelected(value,meta={}) {
      try{
        if (value) localStorage.setItem(AUTO_MAP_TREASURY_LOCK_KEY,'1');
        else localStorage.removeItem(AUTO_MAP_TREASURY_LOCK_KEY);
      }catch(_){}
      recordDiagnostic(value?'treasury-left-once-selected':'treasury-left-once-reset',{
        revision:HK_TREASURY_LOOP_REV,
        reason:String(meta?.reason||''),
        lotId:String(meta?.lotId||'')
      });
      return !!value;
    }

"""
if s.count(anchor)!=1:
    raise SystemExit("autoMapModulesRunning anchor missing")
s=s.replace(anchor,helper+anchor,1)

old_choice_start="""    function autoMapTreasuryChoice() {
      const rows=[...document.querySelectorAll('[data-lot-id^="mf_fair_treasury_room_choose_way_"]')]
"""
new_choice_start="""    function autoMapTreasuryChoice() {
      if (autoMapTreasuryLeftSelected()) return null;

      const rows=[...document.querySelectorAll('[data-lot-id^="mf_fair_treasury_room_choose_way_"]')]
"""
rep(old_choice_start,new_choice_start,"one-shot treasury choice gate")

anchor2="""    function autoMapTreasuryChestRows() {
"""
enter_helper="""    async function autoMapEnterTreasuryLeftPath(choice) {
      if (!choice || autoMapTreasuryLeftSelected()) return false;

      const before=autoMapStateFingerprint();
      setAutoMapTreasuryLeftSelected(true,{
        reason:'before-left-entry',
        lotId:choice.lotId
      });

      autoMapStatus('treasury левый путь',{
        revision:HK_TREASURY_LOOP_REV,
        lotId:choice.lotId,
        x:Math.round(choice.x||0)
      });

      const ok=await autoMapTapAndConfirm(
        choice.element,
        'treasury-left-once-'+choice.lotId,
        choice.cost
      );

      if (ok) return true;

      // Roll back only when the exact same choice screen is still in front.
      // If the screen already changed, keep the latch: this prevents the next
      // visible path from being mistaken for another allowed choice.
      const sameScreen=
        autoMapTreasuryScreenVisible() &&
        autoMapTreasuryChoiceRowsRaw().some(row=>row.lotId===choice.lotId) &&
        autoMapStateFingerprint()===before;
      if (sameScreen) {
        setAutoMapTreasuryLeftSelected(false,{
          reason:'left-entry-failed',
          lotId:choice.lotId
        });
      }
      return ok;
    }

"""
# Need raw choice rows helper too; replace whole current function with split rows + choice.
start=s.index("    function autoMapTreasuryChoice() {")
end=s.index("    function autoMapTreasuryChestRows() {",start)
old_block=s[start:end]
new_block="""    function autoMapTreasuryChoiceRowsRaw() {
      return [...document.querySelectorAll('[data-lot-id^="mf_fair_treasury_room_choose_way_"]')]
        .filter(visible)
        .map(element=>{
          const lotId=String(element.getAttribute('data-lot-id')||'');
          const m=lotId.match(/choose_way_(\d+)/);
          const text=clean(element.innerText||element.textContent||'').trim();
          const costMatch=text.match(/(?:^|\s)(\d{1,4})(?:\s|$)/);
          const rect=element.getBoundingClientRect?.() || {left:99999,top:99999,width:0,height:0};
          return {
            element,
            lotId,
            index:m?Number(m[1]):999,
            cost:costMatch?Number(costMatch[1]):null,
            x:rect.left+rect.width/2,
            y:rect.top+rect.height/2
          };
        })
        .filter(row=>Number.isFinite(row.x) && row.x>=0)
        .sort((a,b)=>a.x-b.x || a.y-b.y || a.index-b.index);
    }

    function autoMapTreasuryChoice() {
      if (autoMapTreasuryLeftSelected()) return null;

      const rows=autoMapTreasuryChoiceRowsRaw();
      const choice=rows[0] || null;
      if (choice) {
        recordDiagnostic('treasury-left-path-selected',{
          revision:HK_TREASURY_LOOP_REV,
          lotId:choice.lotId,
          index:choice.index,
          x:Math.round(choice.x),
          y:Math.round(choice.y),
          visibleChoices:rows.map(row=>({
            lotId:row.lotId,
            index:row.index,
            x:Math.round(row.x),
            y:Math.round(row.y)
          }))
        });
      }
      return choice;
    }

    async function autoMapEnterTreasuryLeftPath(choice) {
      if (!choice || autoMapTreasuryLeftSelected()) return false;

      const before=autoMapStateFingerprint();
      setAutoMapTreasuryLeftSelected(true,{
        reason:'before-left-entry',
        lotId:choice.lotId
      });

      autoMapStatus('treasury левый путь',{
        revision:HK_TREASURY_LOOP_REV,
        lotId:choice.lotId,
        x:Math.round(choice.x||0)
      });

      const ok=await autoMapTapAndConfirm(
        choice.element,
        'treasury-left-once-'+choice.lotId,
        choice.cost
      );

      if (ok) return true;

      // Roll back only when the same left-choice screen is still present.
      const sameScreen=
        autoMapTreasuryScreenVisible() &&
        autoMapTreasuryChoiceRowsRaw().some(row=>row.lotId===choice.lotId) &&
        autoMapStateFingerprint()===before;
      if (sameScreen) {
        setAutoMapTreasuryLeftSelected(false,{
          reason:'left-entry-failed',
          lotId:choice.lotId
        });
      }
      return ok;
    }

"""
s=s[:start]+new_block+s[end:]

# Helper to start first or subsequent journeys with the same lock/session semantics.
anchor3="""    async function runAutoMapTick(source='interval') {
"""
journey_helper="""    async function autoMapStartJourney(label='new-journey') {
      const lockAt=autoMapStartLockAt();
      if (lockAt && Date.now()-lockAt<AUTO_MAP_START_LOCK_MS) {
        autoMapStatus('жду открытия',{elapsedMs:Date.now()-lockAt,label});
        return false;
      }
      if (lockAt) setAutoMapStartLock(0);

      const journey=autoMapJourneyButton();
      if (!journey) return false;

      setAutoMapStartLock(Date.now());
      autoMapStatus(label==='next-journey'?'новая карта':'старт карты',{
        revision:HK_TREASURY_LOOP_REV,
        label
      });

      const started=await autoMapTapAndConfirm(journey,label,1);
      if (started && autoMapMapCards().length>0) {
        setAutoMapSessionStarted(true);
        setAutoMapStartLock(0);
        autoMapNoActiveSince=0;
        autoMapStatus('карта открыта',{
          revision:HK_TREASURY_LOOP_REV,
          label
        });
        recordDiagnostic('treasure-auto-map-next-journey',{
          revision:HK_TREASURY_LOOP_REV,
          label,
          activeCells:autoMapActiveCellCount()
        });
      } else {
        autoMapStatus('жду открытия',{label});
      }
      return started;
    }

"""
if s.count(anchor3)!=1:
    raise SystemExit("runAutoMapTick anchor missing")
s=s.replace(anchor3,journey_helper+anchor3,1)

# Clear treasury one-shot as soon as we are safely back on the map.
old_foreground="""        const foregroundNow=autoMapMiniGameForeground();
        if (foregroundNow) {
"""
new_foreground="""        const foregroundNow=autoMapMiniGameForeground();

        if (treasureGuideScreenVisible() && autoMapTreasuryLeftSelected()) {
          setAutoMapTreasuryLeftSelected(false,{reason:'map-visible'});
        }

        if (foregroundNow) {
"""
rep(old_foreground,new_foreground,"reset treasury latch on map return")

# Replace duplicated first-map start block with helper.
old_first="""          if (!autoMapSessionStarted()) {
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
"""
new_first="""          if (!autoMapSessionStarted()) {
            return await autoMapStartJourney('new-journey');
          }
"""
rep(old_first,new_first,"first journey helper")

# Completed map now rolls into the next journey instead of turning AutoMap off.
old_complete="""          setAutoMapStartLock(0);
          autoMapStatus('ГОТОВО');
          recordDiagnostic('treasure-auto-map-complete',{
            revision:HK_TREASURE_AUTO_MAP_ACTIVE_PRIORITY_REV,
            actions:autoMapActionCount,
            source,
            emptyForMs:emptyFor
          });
          setAutoMapEnabled(false,{reason:'map-complete',preserveStatus:'ГОТОВО'});
          return true;
"""
new_complete="""          setAutoMapStartLock(0);
          setAutoMapSessionStarted(false);
          setAutoMapTreasuryLeftSelected(false,{reason:'map-complete'});
          autoMapNoActiveSince=0;
          autoMapStatus('новая карта',{
            revision:HK_TREASURY_LOOP_REV,
            source,
            emptyForMs:emptyFor
          });
          recordDiagnostic('treasure-auto-map-complete',{
            revision:HK_TREASURY_LOOP_REV,
            actions:autoMapActionCount,
            source,
            emptyForMs:emptyFor,
            nextJourney:true
          });
          return await autoMapStartJourney('next-journey');
"""
rep(old_complete,new_complete,"continuous map loop")

# Treasury path must use the one-shot wrapper, never direct raw tap.
old_choice_branch="""        const choice=autoMapTreasuryChoice();
        if (choice) {
          autoMapStatus('treasury путь');
          return autoMapTapAndConfirm(choice.element,'treasury-'+choice.lotId,choice.cost);
        }
"""
new_choice_branch="""        const choice=autoMapTreasuryChoice();
        if (choice) {
          return await autoMapEnterTreasuryLeftPath(choice);
        }
"""
rep(old_choice_branch,new_choice_branch,"one-shot treasury entry")

# Manual AutoMap OFF clears stale treasury latch too.
old_disable="""        setAutoMapSessionStarted(false);
        setAutoMapStartLock(0);
        recordDiagnostic('treasure-auto-map-toggle',{
"""
new_disable="""        setAutoMapSessionStarted(false);
        setAutoMapStartLock(0);
        setAutoMapTreasuryLeftSelected(false,{reason:'auto-map-off'});
        recordDiagnostic('treasure-auto-map-toggle',{
"""
rep(old_disable,new_disable,"clear treasury latch on off")

rep("      treasuryLeftPathRevision:HK_TREASURY_LEFT_PATH_REV,\n      start,",
    "      treasuryLeftPathRevision:HK_TREASURY_LEFT_PATH_REV,\n      treasuryLoopRevision:HK_TREASURY_LOOP_REV,\n      start,",
    "export treasury loop revision")

for marker in [
    "// @version      1.18.55",
    "const BUILD_VERSION = '1.18.55';",
    "treasury-left-once-continuous-map-20260927-r1",
    "AUTO_MAP_TREASURY_LOCK_KEY",
    "function autoMapTreasuryLeftSelected()",
    "function autoMapTreasuryChoiceRowsRaw()",
    "async function autoMapEnterTreasuryLeftPath",
    "async function autoMapStartJourney",
    "autoMapStartJourney('next-journey')",
    "treasure-auto-map-next-journey",
    "setAutoMapTreasuryLeftSelected(false,{reason:'map-visible'})",
    "treasure-chest-fast-pacing-20260927-r1",
    "battle-achievement-priority-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_TREASURY_LOOP_1_18_55=PASS")
