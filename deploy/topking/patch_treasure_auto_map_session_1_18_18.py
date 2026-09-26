from pathlib import Path
import sys

target=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=target.read_text(encoding="utf-8")

def need(old,label,count=1):
    actual=s.count(old)
    if actual!=count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")

def rep(old,new,label,count=1):
    global s
    need(old,label,count)
    s=s.replace(old,new,count)

rep(
    "// @version      1.18.17",
    "// @version      1.18.18\n"
    "// @release-note Автокарта: теперь сама начинает новую Карту Сокровищ через «Начать новое путешествие» + подтверждение 1, сохраняет состояние прохода через перезагрузку и останавливается только при повторном появлении кнопки после завершения карты.",
    "version"
)
rep("const BUILD_VERSION = '1.18.17';","const BUILD_VERSION = '1.18.18';","build")

rep(
    "  const HK_TREASURE_AUTO_MAP_STABILITY_REV='treasure-auto-map-stability-20260926-r2';",
    "  const HK_TREASURE_AUTO_MAP_STABILITY_REV='treasure-auto-map-stability-20260926-r2';\n"
    "  const HK_TREASURE_AUTO_MAP_SESSION_REV='treasure-auto-map-session-20260926-r3';",
    "session marker"
)

rep(
    """    const AUTO_MAP_STORAGE_KEY='hk:treasure:auto-map:v1';
    const AUTO_MAP_LOOP_MS=420;
""",
    """    const AUTO_MAP_STORAGE_KEY='hk:treasure:auto-map:v1';
    const AUTO_MAP_SESSION_KEY='hk:treasure:auto-map-session:v1';
    const AUTO_MAP_LOOP_MS=420;
""",
    "session key"
)

# Persist whether this AutoMap run has actually entered a map already.
anchor="""    function autoMapModulesRunning() {
"""
helpers=r'''    function autoMapSessionStarted() {
      try{return localStorage.getItem(AUTO_MAP_SESSION_KEY)==='1';}
      catch(_){return false;}
    }

    function setAutoMapSessionStarted(value) {
      try{
        if (value) localStorage.setItem(AUTO_MAP_SESSION_KEY,'1');
        else localStorage.removeItem(AUTO_MAP_SESSION_KEY);
      }catch(_){}
      return !!value;
    }

'''
need(anchor,"modules running anchor")
s=s.replace(anchor,helpers+anchor,1)

# Make toggle updates idempotent to avoid unnecessary DOM churn while recorder is active.
old_update="""      autoMapToggle.style.display=show?'block':'none';
      autoMapToggle.textContent=enabled
        ? 'Автокарта: ВКЛ'+(autoMapLastStatus?' · '+autoMapLastStatus:'')
        : 'Автокарта: ВЫКЛ';
      autoMapToggle.style.background=enabled?'#38c85a':'#292929';
      autoMapToggle.style.color=enabled?'#071b0a':'#fff';
      autoMapToggle.style.borderColor=enabled?'#d8ffe0':'rgba(255,255,255,.8)';
"""
new_update="""      const display=show?'block':'none';
      const label=enabled
        ? 'Автокарта: ВКЛ'+(autoMapLastStatus?' · '+autoMapLastStatus:'')
        : 'Автокарта: ВЫКЛ';
      const background=enabled?'#38c85a':'#292929';
      const color=enabled?'#071b0a':'#fff';
      const borderColor=enabled?'#d8ffe0':'rgba(255,255,255,.8)';
      if (autoMapToggle.style.display!==display) autoMapToggle.style.display=display;
      if (autoMapToggle.textContent!==label) autoMapToggle.textContent=label;
      if (autoMapToggle.style.background!==background) autoMapToggle.style.background=background;
      if (autoMapToggle.style.color!==color) autoMapToggle.style.color=color;
      if (autoMapToggle.style.borderColor!==borderColor) autoMapToggle.style.borderColor=borderColor;
"""
rep(old_update,new_update,"idempotent toggle")

# Journey button becomes start-before-map or finish-after-map based on session state.
old_journey="""        // A completed Treasure Map is the terminal state: do not start a new map.
        if (treasureGuideScreenVisible() && autoMapJourneyButton()) {
          autoMapStatus('ГОТОВО');
          recordDiagnostic('treasure-auto-map-complete',{
            revision:HK_TREASURE_AUTO_MAP_REV,
            actions:autoMapActionCount,
            source
          });
          setAutoMapEnabled(false,{reason:'map-complete',preserveStatus:'ГОТОВО'});
          return true;
        }

        // Normal map traversal: lowest currently active slot first, then rescan.
        if (treasureGuideScreenVisible()) {
          const target=autoMapMapCards()[0];
"""
new_journey="""        // The same game button is present both before the first map and after the
        // completed map. Persist session state so reloads cannot start a second map.
        if (treasureGuideScreenVisible() && autoMapJourneyButton()) {
          if (!autoMapSessionStarted()) {
            const journey=autoMapJourneyButton();
            autoMapStatus('старт карты');
            const started=await autoMapTapAndConfirm(journey,'new-journey',1);
            if (started) {
              setAutoMapSessionStarted(true);
              autoMapStatus('карта открыта');
            }
            return started;
          }

          autoMapStatus('ГОТОВО');
          recordDiagnostic('treasure-auto-map-complete',{
            revision:HK_TREASURE_AUTO_MAP_SESSION_REV,
            actions:autoMapActionCount,
            source
          });
          setAutoMapEnabled(false,{reason:'map-complete',preserveStatus:'ГОТОВО'});
          return true;
        }

        // Normal map traversal: lowest currently active slot first, then rescan.
        if (treasureGuideScreenVisible()) {
          const target=autoMapMapCards()[0];
"""
rep(old_journey,new_journey,"start vs finish journey")

# Seeing an active map cell proves the session is underway.
rep(
    """          if (target) {
            autoMapCurrentLot=target.lotId;
""",
    """          if (target) {
            if (!autoMapSessionStarted()) setAutoMapSessionStarted(true);
            autoMapCurrentLot=target.lotId;
""",
    "mark session on map target"
)

# Entering any non-map minigame also proves session is underway after reload.
rep(
    """        // Treasury room after the boss: first choose route 1 (recorded canonical run),
        // then open the big chest, collect reward and leave normally.
        const choice=autoMapTreasuryChoice();
""",
    """        // Any non-map room while AutoMap is active belongs to the current map.
        if (!treasureGuideScreenVisible() && !autoMapSessionStarted()) {
          setAutoMapSessionStarted(true);
        }

        // Treasury room after the boss: first choose route 1 (recorded canonical run),
        // then open the big chest, collect reward and leave normally.
        const choice=autoMapTreasuryChoice();
""",
    "mark session in minigame"
)

# Manual enable initializes a fresh session only when there is no active saved one.
rep(
    """      if (value) {
        autoMapActionCount=0;
        autoMapLastStatus='';
        autoMapEnableModules();
""",
    """      if (value) {
        autoMapActionCount=0;
        autoMapLastStatus='';
        if (!autoMapSessionStarted()) {
          // If enabling in the middle of an already-open map/minigame, infer that
          // the current session has started. A visible "new journey" button means
          // we are still before the map.
          const alreadyInside=!autoMapJourneyButton();
          setAutoMapSessionStarted(alreadyInside);
        }
        autoMapEnableModules();
""",
    "enable session inference"
)

# Stop/completion clears session marker after all work is done.
rep(
    """        if (finalStatus) autoMapLastStatus=finalStatus;
        else if (meta?.reason && meta.reason!=='map-complete') autoMapLastStatus='стоп';
""",
    """        if (finalStatus) autoMapLastStatus=finalStatus;
        else if (meta?.reason && meta.reason!=='map-complete') autoMapLastStatus='стоп';
        setAutoMapSessionStarted(false);
""",
    "clear session on stop"
)

# Export session state.
rep(
    """      treasureAutoMapRevision:HK_TREASURE_AUTO_MAP_REV,
      start,
""",
    """      treasureAutoMapRevision:HK_TREASURE_AUTO_MAP_REV,
      treasureAutoMapSessionRevision:HK_TREASURE_AUTO_MAP_SESSION_REV,
      start,
""",
    "export session revision"
)

for marker in [
    "// @version      1.18.18",
    "const BUILD_VERSION = '1.18.18';",
    "treasure-auto-map-orchestrator-20260926-r1",
    "treasure-auto-map-stability-20260926-r2",
    "treasure-auto-map-session-20260926-r3",
    "AUTO_MAP_SESSION_KEY",
    "new-journey",
    "setAutoMapSessionStarted(true)",
    "preserveStatus:'ГОТОВО'",
    "rumors-hunter-coordinator-kokkaras-v40-20260926-r4",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("TREASURE_AUTO_MAP_SESSION_1_18_18=PASS")
