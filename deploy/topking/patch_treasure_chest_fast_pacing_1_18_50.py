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

rep("// @version      1.18.49",
    "// @version      1.18.50\n// @release-note Сундуки: немного ускорены только задержки режима Автосундуков — поиск цели, открытие карточки, подтверждение, ожидание результата и сбор награды. Логика выбора сундуков, проверки доступности, защита от ложных сундуков на карте и таймауты подтверждения не менялись.",
    "version")
rep("const BUILD_VERSION = '1.18.49';",
    "const BUILD_VERSION = '1.18.50';",
    "build")
rep("  const HK_TREASURE_LIGHTS_OUTER_MODAL_REV='treasure-lights-outer-modal-20260927-r1';",
    "  const HK_TREASURE_LIGHTS_OUTER_MODAL_REV='treasure-lights-outer-modal-20260927-r1';\n  const HK_TREASURE_CHEST_FAST_PACING_REV='treasure-chest-fast-pacing-20260927-r1';",
    "revision")

anchor="""    async function traderHumanPause(stage='scan',data={}) {
"""
helper="""    async function chestHumanPause(stage='scan',data={}) {
      const ranges={
        scan:[600,950],
        aim:[380,650],
        confirm:[650,1050],
        settle:[950,1500],
        reward:[420,700]
      };
      const range=ranges[stage] || ranges.scan;
      const waitMs=minigameRandomMs(range[0],range[1]);
      recordDiagnostic('treasure-chest-human-pause',{
        revision:HK_TREASURE_CHEST_FAST_PACING_REV,
        stage,
        waitMs,
        ...data
      });
      await new Promise(resolve=>setTimeout(resolve,waitMs));
      return waitMs;
    }

"""
if s.count(anchor)!=1:
    raise SystemExit("traderHumanPause anchor missing")
s=s.replace(anchor,helper+anchor,1)

rep("        await minigameHumanPause('reward',{module:'chests',index:i+1});",
    "        await chestHumanPause('reward',{module:'chests',index:i+1});",
    "chest reward pause")
rep("        await minigameHumanPause('settle',{module:'chest-reward',index:i+1});",
    "        await chestHumanPause('settle',{module:'chest-reward',index:i+1});",
    "chest reward settle")
rep("      await minigameHumanPause('scan',{module:'chests'});",
    "      await chestHumanPause('scan',{module:'chests'});",
    "chest scan pause")
rep("        await minigameHumanPause('aim',{module:'chests',lotId:target.lotId});",
    "        await chestHumanPause('aim',{module:'chests',lotId:target.lotId});",
    "chest aim pause")
rep("        await minigameHumanPause('confirm',{module:'chests',lotId:target.lotId});",
    "        await chestHumanPause('confirm',{module:'chests',lotId:target.lotId});",
    "chest confirm pause")
rep("        await minigameHumanPause('settle',{module:'chests',lotId:target.lotId});",
    "        await chestHumanPause('settle',{module:'chests',lotId:target.lotId});",
    "chest settle pause")
rep("        setTimeout(checkPuzzle,minigameRandomMs(1400,2200));",
    "        setTimeout(checkPuzzle,minigameRandomMs(950,1450));",
    "chest next-step pause")

rep("      treasureLightsOuterModalRevision:HK_TREASURE_LIGHTS_OUTER_MODAL_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "      treasureLightsOuterModalRevision:HK_TREASURE_LIGHTS_OUTER_MODAL_REV,\n      treasureChestFastPacingRevision:HK_TREASURE_CHEST_FAST_PACING_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "export chest pacing revision")

for marker in [
    "// @version      1.18.50",
    "const BUILD_VERSION = '1.18.50';",
    "treasure-chest-fast-pacing-20260927-r1",
    "async function chestHumanPause",
    "scan:[600,950]",
    "aim:[380,650]",
    "confirm:[650,1050]",
    "settle:[950,1500]",
    "reward:[420,700]",
    "minigameRandomMs(950,1450)",
    "treasure-lights-outer-modal-20260927-r1",
    "treasure-chest-map-foreground-guard-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_CHEST_FAST_PACING_1_18_50=PASS")
