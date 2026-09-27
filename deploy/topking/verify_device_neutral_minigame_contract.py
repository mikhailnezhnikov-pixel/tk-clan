from pathlib import Path
import sys

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

if "device-neutral-minigame-20260928-r1" in s:
    helper=section("async function minigameDevicePause","function minigameRecentHttpError")
    for marker in [
        "scan:350",
        "aim:250",
        "confirm:450",
        "settle:700",
        "reward:350",
        "map:450",
        "async function waitDeviceNeutralCondition",
        "async function deviceNeutralActivate",
        "element.click()",
        "dispatchAutoMapTap(element,label+'-fallback')",
        "await waitDeviceNeutralCondition",
    ]:
        if marker not in helper:
            raise SystemExit(f"device-neutral helper contract broken: {marker}")

    for forbidden in [
        "navigator.userAgent",
        "window.innerWidth",
        "matchMedia(",
        "ontouchstart",
        "minigameRandomMs(",
        "Math.random(",
    ]:
        if forbidden in helper:
            raise SystemExit(f"device-neutral helper became platform/random dependent: {forbidden}")

    # Historical module helpers remain for backward-compatible contracts, but
    # all normal pacing enters the same deterministic scheduler.
    for name,next_name in [
        ("async function minigameHumanPause","async function chestHumanPause"),
        ("async function chestHumanPause","async function traderHumanPause"),
        ("async function traderHumanPause","async function fishingHumanPause"),
        ("async function fishingHumanPause","async function minigameDevicePause"),
    ]:
        block=section(name,next_name)
        if "return minigameDevicePause(stage," not in block:
            raise SystemExit(f"{name} does not delegate to device-neutral pacing")

    lights=section("async function runLightsModalStep","function lightsRewardElement")
    for marker in [
        "clearStaleLightsModalBeforeStep(runId,slot)",
        "deviceNeutralActivate(",
        "'lights-open-'+slot",
        "'lights-confirm-cost-'+slot",
        "lightsBoardSignature()!==before",
        "waitLightsBoardChange(before,runId,3200)",
        "closeLightsModalAfterStateChange(runId,before,slot,1800)",
        "field-changed-modal-closed-device-neutral",
    ]:
        if marker not in lights:
            raise SystemExit(f"device-neutral lights contract broken: {marker}")

    # A dispatched click is never enough by itself: confirmation must be tied
    # to observable UI/board state.
    if "const accepted=()=> {" not in lights or "lightsAcknowledgeButton(current)" not in lights:
        raise SystemExit("lights confirmation is not state-verified")

    for marker in [
        "const BATTLE_AUTO_SETTLE_MS = 700;",
        "const LIGHTS_AUTO_SETTLE_MS = 700;",
        "const FISHING_MIN_NEXT_ACTION_GAP_MS = 1200;",
        "const TRADER_MIN_NEXT_ACTION_GAP_MS = 1200;",
        "const AUTO_MAP_ACTION_GAP_MS=1200;",
    ]:
        if marker not in s:
            raise SystemExit(f"device-neutral cadence contract broken: {marker}")

print("DEVICE_NEUTRAL_MINIGAME_CONTRACT=PASS")
