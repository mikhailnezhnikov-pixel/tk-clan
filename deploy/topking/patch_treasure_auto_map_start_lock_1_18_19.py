from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def r(a,b,label):
    global s
    if s.count(a)!=1:
        raise SystemExit(f"{label}: {s.count(a)}")
    s=s.replace(a,b,1)

r("// @version      1.18.18",
  "// @version      1.18.19\n// @release-note Автокарта: исправлен повторный запуск новой карты. Действия Автокарты теперь дают ровно один click; после первого запуска ставится start-lock и повторный «Начать новое путешествие» запрещён до появления активной карты либо истечения безопасного ожидания.",
  "version")
r("const BUILD_VERSION = '1.18.18';","const BUILD_VERSION = '1.18.19';","build")
r("  const HK_TREASURE_AUTO_MAP_SESSION_REV='treasure-auto-map-session-20260926-r3';",
  "  const HK_TREASURE_AUTO_MAP_SESSION_REV='treasure-auto-map-session-20260926-r3';\n  const HK_TREASURE_AUTO_MAP_START_LOCK_REV='treasure-auto-map-start-lock-20260926-r4';",
  "revision")

r("    const AUTO_MAP_SESSION_KEY='hk:treasure:auto-map-session:v1';\n    const AUTO_MAP_LOOP_MS=420;",
  "    const AUTO_MAP_SESSION_KEY='hk:treasure:auto-map-session:v1';\n    const AUTO_MAP_START_LOCK_KEY='hk:treasure:auto-map-start-lock:v1';\n    const AUTO_MAP_START_LOCK_MS=9000;\n    const AUTO_MAP_LOOP_MS=420;",
  "lock constants")

anchor="    function autoMapFindTextButton(pattern,root=document) {"
if s.count(anchor)!=1: raise SystemExit("tap anchor")
helper="""    function autoMapStartLockAt() {
      try{return Number(localStorage.getItem(AUTO_MAP_START_LOCK_KEY)||0)||0;}
      catch(_){return 0;}
    }

    function setAutoMapStartLock(value) {
      try{
        if (value) localStorage.setItem(AUTO_MAP_START_LOCK_KEY,String(value));
        else localStorage.removeItem(AUTO_MAP_START_LOCK_KEY);
      }catch(_){}
    }

    function dispatchAutoMapTap(element,label='auto-map-tap') {
      if (!element || !visible(element)) return false;
      const clickable=element.closest?.('button,[role="button"],a') || element;
      try { clickable.click(); }
      catch (_) { return false; }
      recordDiagnostic('treasure-auto-map-tap',{
        revision:HK_TREASURE_AUTO_MAP_START_LOCK_REV,
        label,
        tag:clickable.tagName||''
      });
      return true;
    }

"""
s=s.replace(anchor,helper+anchor,1)

r("      if (!dispatchBattleTap(element,'auto-map-'+label)) {",
  "      if (!dispatchAutoMapTap(element,'auto-map-'+label)) {","single target")
r("      if (!dispatchBattleTap(action,'auto-map-confirm-'+label)) {",
  "      if (!dispatchAutoMapTap(action,'auto-map-confirm-'+label)) {","single confirm")
r("      const ok=dispatchBattleTap(button,'auto-map-reward-'+text.slice(0,30));",
  "      const ok=dispatchAutoMapTap(button,'auto-map-reward-'+text.slice(0,30));","single reward")

old="""        if (treasureGuideScreenVisible() && autoMapJourneyButton()) {
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
"""
new="""        if (treasureGuideScreenVisible() && autoMapJourneyButton()) {
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
"""
r(old,new,"journey lock")

r("          if (target) {\n            if (!autoMapSessionStarted()) setAutoMapSessionStarted(true);",
  "          if (target) {\n            if (!autoMapSessionStarted()) setAutoMapSessionStarted(true);\n            setAutoMapStartLock(0);",
  "map unlock")

r("        setAutoMapSessionStarted(false);",
  "        setAutoMapSessionStarted(false);\n        setAutoMapStartLock(0);",
  "stop unlock")

r("      treasureAutoMapSessionRevision:HK_TREASURE_AUTO_MAP_SESSION_REV,\n      start,",
  "      treasureAutoMapSessionRevision:HK_TREASURE_AUTO_MAP_SESSION_REV,\n      treasureAutoMapStartLockRevision:HK_TREASURE_AUTO_MAP_START_LOCK_REV,\n      start,",
  "export revision")

for x in [
  "// @version      1.18.19",
  "const BUILD_VERSION = '1.18.19';",
  "treasure-auto-map-start-lock-20260926-r4",
  "dispatchAutoMapTap",
  "AUTO_MAP_START_LOCK_MS=9000",
  "setAutoMapStartLock(Date.now())",
  "treasure-auto-map-session-20260926-r3",
  "treasure-auto-map-stability-20260926-r2",
  "treasure-auto-map-orchestrator-20260926-r1"
]:
    if x not in s: raise SystemExit("missing "+x)

p.write_text(s,encoding="utf-8")
print("TREASURE_AUTO_MAP_START_LOCK_1_18_19=PASS")
