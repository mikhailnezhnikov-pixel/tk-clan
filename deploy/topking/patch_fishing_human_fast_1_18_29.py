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

rep("// @version      1.18.28",
    "// @version      1.18.29\n// @release-note Рыбалка: ускорен только темп покупки слотов. Сохраняется последовательность «перескан → выбор → открытие → пауза → подтверждение → ответ сервера → следующий слот», но без избыточных общих задержек. Целевой темп — около 2–3 секунд на слот при нормальном ответе сервера.",
    "version")
rep("const BUILD_VERSION = '1.18.28';",
    "const BUILD_VERSION = '1.18.29';",
    "build")
rep("  const HK_MINIGAME_SINGLE_TAP_REV='minigame-single-tap-20260927-r1';",
    "  const HK_MINIGAME_SINGLE_TAP_REV='minigame-single-tap-20260927-r1';\n  const HK_FISHING_HUMAN_FAST_REV='fishing-human-fast-20260927-r1';",
    "revision")

rep("    const FISHING_MIN_NEXT_ACTION_GAP_MS = 2800;",
    "    const FISHING_MIN_NEXT_ACTION_GAP_MS = 1100;",
    "fishing action gap")

anchor="""    function minigameRecentHttpError(since=0,windowMs=8000) {
"""
if s.count(anchor)!=1:
    raise SystemExit("minigameRecentHttpError anchor missing")
helper="""    async function fishingHumanPause(stage='scan',data={}) {
      const ranges={
        scan:[250,450],
        aim:[180,320],
        confirm:[350,650],
        settle:[600,900],
        reward:[300,500]
      };
      const range=ranges[stage] || ranges.scan;
      const waitMs=minigameRandomMs(range[0],range[1]);
      recordDiagnostic('fishing-human-pause',{
        revision:HK_FISHING_HUMAN_FAST_REV,
        stage,
        waitMs,
        ...data
      });
      await new Promise(resolve=>setTimeout(resolve,waitMs));
      return waitMs;
    }

"""
s=s.replace(anchor,helper+anchor,1)

replacements=[
("await minigameHumanPause('scan',{module:'fishing'});",
 "await fishingHumanPause('scan',{module:'fishing'});",
 "fishing scan"),
("await minigameHumanPause('aim',{module:'fishing',lotId:target.lotId});",
 "await fishingHumanPause('aim',{module:'fishing',lotId:target.lotId});",
 "fishing aim"),
("await minigameHumanPause('confirm',{module:'fishing',lotId:target.lotId});",
 "await fishingHumanPause('confirm',{module:'fishing',lotId:target.lotId});",
 "fishing confirm"),
("await minigameHumanPause('settle',{module:'fishing',lotId:target.lotId});",
 "await fishingHumanPause('settle',{module:'fishing',lotId:target.lotId});",
 "fishing settle"),
("await minigameHumanPause('reward',{module:'fishing',index:i+1});",
 "await fishingHumanPause('reward',{module:'fishing',index:i+1});",
 "fishing reward"),
("await minigameHumanPause('settle',{module:'fishing-reward',index:i+1});",
 "await fishingHumanPause('settle',{module:'fishing-reward',index:i+1});",
 "fishing reward settle"),
]
for a,b,label in replacements:
    rep(a,b,label)

rep("      minigameSingleTapRevision:HK_MINIGAME_SINGLE_TAP_REV,\n      start,",
    "      minigameSingleTapRevision:HK_MINIGAME_SINGLE_TAP_REV,\n      fishingHumanFastRevision:HK_FISHING_HUMAN_FAST_REV,\n      start,",
    "export revision")

for marker in [
    "// @version      1.18.29",
    "const BUILD_VERSION = '1.18.29';",
    "fishing-human-fast-20260927-r1",
    "FISHING_MIN_NEXT_ACTION_GAP_MS = 1100",
    "async function fishingHumanPause",
    "scan:[250,450]",
    "confirm:[350,650]",
    "settle:[600,900]",
    "await fishingHumanPause('scan',{module:'fishing'})",
    "treasure-final-reward-handoff-20260927-r1",
    "fishing-visible-casts-20260927-r1",
    "minigame-single-tap-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("FISHING_HUMAN_FAST_1_18_29=PASS")
