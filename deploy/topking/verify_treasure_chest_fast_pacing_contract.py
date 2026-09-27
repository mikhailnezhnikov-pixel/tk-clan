from pathlib import Path
import sys,re

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def section(start,end):
    a=s.find(start)
    if a<0:
        raise SystemExit(f"missing section start: {start}")
    b=s.find(end,a+len(start))
    if b<0:
        raise SystemExit(f"missing section end: {end}")
    return s[a:b]

if "treasure-chest-fast-pacing-20260927-r1" in s:
    helper=section("async function chestHumanPause","async function traderHumanPause")
    required={
        "scan:[600,950]":"scan",
        "aim:[380,650]":"aim",
        "confirm:[650,1050]":"confirm",
        "settle:[950,1500]":"settle",
        "reward:[420,700]":"reward",
        "HK_TREASURE_CHEST_FAST_PACING_REV":"revision",
    }
    for marker,label in required.items():
        if marker not in helper:
            raise SystemExit(f"chest pacing contract broken: {label}")

    generic=section("async function minigameHumanPause","async function chestHumanPause")
    for marker in [
        "scan:[850,1450]",
        "aim:[550,950]",
        "confirm:[950,1650]",
        "settle:[1500,2400]",
        "reward:[650,1050]",
    ]:
        if marker not in generic:
            raise SystemExit(f"global minigame pacing was changed: {marker}")

    rewards=section("async function dismissTreasureRewards","async function tapTreasureActionFallback")
    if "chestHumanPause('reward'" not in rewards or "chestHumanPause('settle'" not in rewards:
        raise SystemExit("chest reward pacing did not use chest-specific helper")

    runner=section("async function runTreasureChestAuto","function battleVictoryElement")
    for marker in [
        "chestHumanPause('scan'",
        "chestHumanPause('aim'",
        "chestHumanPause('confirm'",
        "chestHumanPause('settle'",
        "minigameRandomMs(950,1450)",
    ]:
        if marker not in runner:
            raise SystemExit(f"chest runner pacing contract broken: {marker}")

    # Safety behaviour must remain intact while speeding up delays.
    for marker in [
        "treasureChestBlockedByForegroundMap()",
        "waitTreasureModal(target.cost,runId)",
        "waitTreasureActionButton(modal,target.cost,runId)",
        "CHEST_ACTION_TIMEOUT_MS",
        "dismissTreasureRewards(runId)",
    ]:
        if marker not in runner:
            raise SystemExit(f"chest safety contract broken: {marker}")

print("TREASURE_CHEST_FAST_PACING_CONTRACT=PASS")
