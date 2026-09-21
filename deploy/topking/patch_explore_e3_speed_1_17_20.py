from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")

required=[
    "// @version      1.17.19",
    "const BUILD_VERSION = '1.17.19';",
    "const HK_CORE_REVISION = 'core-20260921-r21-buildings-native-sync';",
    "const HK_EXPLORE_CANON_REV='explore-e3-single-20260920-r9-runner';",
    "function exploreSettings()",
    "function exploreSaveSettings(x)",
    "async function exploreE3Delay(settings,type)",
]
for marker in required:
    if marker not in s:
        raise SystemExit(f"missing expected marker: {marker}")

s=s.replace("// @version      1.17.19","// @version      1.17.20",1)
s=s.replace(
    "// @release-note После открытия зданий HK теперь проверяет native-store игры и синхронизирует карту; при необходимости выполняется одна безопасная перезагрузка.",
    "// @release-note Исследование E3 слегка ускорено: стандартные паузы между действиями и боями уменьшены без снятия проверок состояния.\n"
    "// @release-note После открытия зданий HK теперь проверяет native-store игры и синхронизирует карту; при необходимости выполняется одна безопасная перезагрузка.",
    1,
)
s=s.replace("const BUILD_VERSION = '1.17.19';","const BUILD_VERSION = '1.17.20';",1)
s=s.replace(
    "const HK_CORE_REVISION = 'core-20260921-r21-buildings-native-sync';",
    "const HK_CORE_REVISION = 'core-20260921-r22-explore-speed-tune';",
    1,
)
s=s.replace(
    "const HK_EXPLORE_CANON_REV='explore-e3-single-20260920-r9-runner';",
    "const HK_EXPLORE_CANON_REV='explore-e3-single-20260920-r9-runner';\n"
    "  const HK_EXPLORE_SPEED_REV='explore-e3-speed-20260921-r1';",
    1,
)

old_head="""  function exploreSettings(){
    const x=load().exploreCanonSettings||{},clamp=(v,a,b,d)=>Number.isFinite(Number(v))?Math.min(b,Math.max(a,Math.trunc(Number(v)))):d;
    const st=Array.isArray(x.startTiers)?[...new Set(x.startTiers.map(Number).filter(v=>Number.isInteger(v)&&v>=0&&v<=7))]:[0,1,2];
"""
new_head="""  function exploreSettings(){
    const x=load().exploreCanonSettings||{},clamp=(v,a,b,d)=>Number.isFinite(Number(v))?Math.min(b,Math.max(a,Math.trunc(Number(v)))):d;
    const legacyDefaultSpeed=String(x.speedProfileRev||'')!==HK_EXPLORE_SPEED_REV
      && Number(x.actionDelayMinMs??1000)===1000
      && Number(x.actionDelayMaxMs??3000)===3000
      && Number(x.battleDelayMs??1000)===1000;
    const actionDelayMinMs=legacyDefaultSpeed?700:clamp(x.actionDelayMinMs,0,60000,700);
    const actionDelayMaxMs=legacyDefaultSpeed?2000:clamp(x.actionDelayMaxMs,0,60000,2000);
    const battleDelayMs=legacyDefaultSpeed?700:clamp(x.battleDelayMs,0,60000,700);
    const st=Array.isArray(x.startTiers)?[...new Set(x.startTiers.map(Number).filter(v=>Number.isInteger(v)&&v>=0&&v<=7))]:[0,1,2];
"""
if old_head not in s:
    raise SystemExit("exploreSettings head not found")
s=s.replace(old_head,new_head,1)

old_delays="""      nextTierLevel:explorePriority(x.nextTierLevel||'max'),totalEvents:explorePriority(x.totalEvents||'any'),
      actionDelayMinMs:clamp(x.actionDelayMinMs,0,60000,1000),actionDelayMaxMs:clamp(x.actionDelayMaxMs,0,60000,3000),
      battleDelayMs:clamp(x.battleDelayMs,0,60000,1000),betweenBuildingsDelayMinMs:clamp(x.betweenBuildingsDelayMinMs,0,120000,2000),
      betweenBuildingsDelayMaxMs:clamp(x.betweenBuildingsDelayMaxMs,0,120000,7000),buyMissingMaterials:x.buyMissingMaterials===true,
"""
new_delays="""      nextTierLevel:explorePriority(x.nextTierLevel||'max'),totalEvents:explorePriority(x.totalEvents||'any'),
      actionDelayMinMs,actionDelayMaxMs,battleDelayMs,
      betweenBuildingsDelayMinMs:clamp(x.betweenBuildingsDelayMinMs,0,120000,2000),
      betweenBuildingsDelayMaxMs:clamp(x.betweenBuildingsDelayMaxMs,0,120000,7000),buyMissingMaterials:x.buyMissingMaterials===true,
      speedProfileRev:HK_EXPLORE_SPEED_REV,
"""
if old_delays not in s:
    raise SystemExit("explore delay settings block not found")
s=s.replace(old_delays,new_delays,1)

old_save="""    if(x.actionDelayMaxMs<x.actionDelayMinMs)x.actionDelayMaxMs=x.actionDelayMinMs;
    if(x.betweenBuildingsDelayMaxMs<x.betweenBuildingsDelayMinMs)x.betweenBuildingsDelayMaxMs=x.betweenBuildingsDelayMinMs;
    x.exploreTargetTier=targetActionsAllowed;if(!x.exploreTargetTier)x.exploreTargetBattles=false;
    save({exploreCanonSettings:x});return x;
"""
new_save="""    if(x.actionDelayMaxMs<x.actionDelayMinMs)x.actionDelayMaxMs=x.actionDelayMinMs;
    if(x.betweenBuildingsDelayMaxMs<x.betweenBuildingsDelayMinMs)x.betweenBuildingsDelayMaxMs=x.betweenBuildingsDelayMinMs;
    x.speedProfileRev=HK_EXPLORE_SPEED_REV;
    x.exploreTargetTier=targetActionsAllowed;if(!x.exploreTargetTier)x.exploreTargetBattles=false;
    save({exploreCanonSettings:x});return x;
"""
if old_save not in s:
    raise SystemExit("explore save block not found")
s=s.replace(old_save,new_save,1)

s=s.replace(
    "either('Задержки будущего запуска','Future run delays')",
    "either('Задержки выполнения','Execution delays')",
    1,
)

for marker in [
    "// @version      1.17.20",
    "const BUILD_VERSION = '1.17.20';",
    "core-20260921-r22-explore-speed-tune",
    "explore-e3-speed-20260921-r1",
    "legacyDefaultSpeed",
    "actionDelayMinMs=legacyDefaultSpeed?700",
    "actionDelayMaxMs=legacyDefaultSpeed?2000",
    "battleDelayMs=legacyDefaultSpeed?700",
    "x.speedProfileRev=HK_EXPLORE_SPEED_REV;",
    "Задержки выполнения",
    "buildings-native-sync-20260921-r1",
    "maps-shared-runtime-20260921-r7-safe5",
    "AUTH_PASSIVE_SAFETY_R1",
]:
    if marker not in s:
        raise SystemExit(f"post-patch marker missing: {marker}")

PATH.write_text(s,encoding="utf-8")
print("EXPLORE_E3_SPEED_R1_PATCH=PASS")
