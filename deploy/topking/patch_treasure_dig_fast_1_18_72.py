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

rep(
    "// @version      1.18.71",
    "// @version      1.18.72\n"
    "// @release-note Карта сокровищ — Место раскопок: убраны длинные искусственные паузы только для раскопок. Открытие клетки, подтверждение стоимости 5 ягод, ожидание результата и переход к следующему действию теперь выполняются быстрым отдельным темпом; обычные сундуки и защитные таймауты не ускорялись.",
    "version"
)
rep("const BUILD_VERSION = '1.18.71';","const BUILD_VERSION = '1.18.72';","build")

anchor="  const HK_TREASURE_CHEST_FAST_PACING_REV='treasure-chest-fast-pacing-20260927-r1';"
rep(
    anchor,
    anchor+"\n  const HK_TREASURE_DIG_FAST_REV='treasure-dig-fast-pacing-20260928-r1';",
    "dig fast revision"
)

helper_anchor="""    async function chestHumanPause(stage='scan',data={}) {
"""
if s.count(helper_anchor)!=1:
    raise SystemExit("chestHumanPause anchor missing")

helper="""    async function chestDigPause(stage='scan',data={}) {
      const ranges={
        scan:[90,160],
        aim:[70,130],
        confirm:[110,190],
        settle:[180,300],
        reward:[100,180]
      };
      const range=ranges[stage] || ranges.scan;
      const waitMs=minigameRandomMs(range[0],range[1]);
      recordDiagnostic('treasure-dig-fast-pause',{
        revision:HK_TREASURE_DIG_FAST_REV,
        stage,
        waitMs,
        ...data
      });
      await new Promise(resolve=>setTimeout(resolve,waitMs));
      return waitMs;
    }

"""
s=s.replace(helper_anchor,helper+helper_anchor,1)

# Digging spots use a dedicated fast path. Other chest types retain 1.18.50 pacing.
rep(
    "      await chestHumanPause('scan',{module:'chests'});",
    "      await (target?.digging ? chestDigPause('scan',{module:'chests',lotId:target.lotId}) : chestHumanPause('scan',{module:'chests'}));",
    "dig scan pacing"
)
rep(
    "        await chestHumanPause('aim',{module:'chests',lotId:target.lotId});",
    "        await (target.digging ? chestDigPause('aim',{module:'chests',lotId:target.lotId}) : chestHumanPause('aim',{module:'chests',lotId:target.lotId}));",
    "dig aim pacing"
)
rep(
    "        await chestHumanPause('confirm',{module:'chests',lotId:target.lotId});",
    "        await (target.digging ? chestDigPause('confirm',{module:'chests',lotId:target.lotId}) : chestHumanPause('confirm',{module:'chests',lotId:target.lotId}));",
    "dig confirm pacing"
)
rep(
    "        await chestHumanPause('settle',{module:'chests',lotId:target.lotId});",
    "        await (target.digging ? chestDigPause('settle',{module:'chests',lotId:target.lotId}) : chestHumanPause('settle',{module:'chests',lotId:target.lotId}));",
    "dig settle pacing"
)
rep(
    "        setTimeout(checkPuzzle,minigameRandomMs(950,1450));",
    "        setTimeout(checkPuzzle,target?.digging ? minigameRandomMs(180,320) : minigameRandomMs(950,1450));",
    "dig next action pacing"
)

# Export revision for diagnostics.
export_anchor="      treasureChestFastPacingRevision:HK_TREASURE_CHEST_FAST_PACING_REV,"
if s.count(export_anchor)!=1:
    raise SystemExit("chest pacing export anchor missing")
s=s.replace(
    export_anchor,
    export_anchor+"\n      treasureDigFastRevision:HK_TREASURE_DIG_FAST_REV,",
    1
)

for marker in [
    "// @version      1.18.72",
    "const BUILD_VERSION = '1.18.72';",
    "treasure-dig-fast-pacing-20260928-r1",
    "async function chestDigPause",
    "scan:[90,160]",
    "aim:[70,130]",
    "confirm:[110,190]",
    "settle:[180,300]",
    "target?.digging ? chestDigPause('scan'",
    "target.digging ? chestDigPause('confirm'",
    "target?.digging ? minigameRandomMs(180,320)",
    "treasureDigFastRevision:HK_TREASURE_DIG_FAST_REV",
    "treasure-chest-fast-pacing-20260927-r1",
    "trader-receipt-ack-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_DIG_FAST_1_18_72=PASS")
