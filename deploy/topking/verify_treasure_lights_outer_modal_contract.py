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

if "treasure-lights-outer-modal-20260927-r1" in s:
    helper=section("function lightsOuterModalRoot()","function lightsModalRoot()")
    for marker in [
        "let node=seed;",
        "node=node.parentElement",
        "lightsModalCloseButton(node) || autoMapModalCloseButton(node)",
        "rows.find(row=>row.close)",
        "treasure-lights-outer-modal-root",
    ]:
        if marker not in helper:
            raise SystemExit(f"outer lamp modal contract broken: {marker}")

    root=section("function lightsModalRoot()","async function waitLightsModal")
    if "const outer=lightsOuterModalRoot();" not in root or "if (outer) return outer;" not in root:
        raise SystemExit("outer lamp modal contract broken: lightsModalRoot must prefer outer dialog")

    stale=section("async function clearStaleLightsModalBeforeStep","async function runLightsModalStep")
    for marker in [
        "const outer=lightsOuterModalRoot();",
        "lights-clear-stale-outer-close",
        "lights-clear-stale-outer-corner",
        "if (!lightsModalRoot()) return true;",
    ]:
        if marker not in stale:
            raise SystemExit(f"outer lamp stale cleanup contract broken: {marker}")

    for forbidden in [
        "const outer=treasureCenteredModalRoot();",
        "lightsPurchaseButton(",
        "tapLightsPurchaseFallback(",
    ]:
        if forbidden in stale:
            raise SystemExit(f"outer lamp stale cleanup regressed: {forbidden}")


if "minigame-tap-isolation-lights-recovery-20260928-r1" in s:
    step=section("async function runLightsModalStep","function lightsRewardElement")
    if "lights-confirm-ack-before-board-reward-gate-20260928-r1" in s:
        recovery_markers=[
            "tapLightsPurchaseFallback(fallbackRoot,slot)",
            "waitDeviceNeutralCondition(purchaseAccepted,1600,60)",
            "lights-purchase-coordinate-fallback",
            "HK_LIGHTS_CONFIRM_STATE_MACHINE_REV",
            "lights-confirm-ack-",
        ]
    else:
        recovery_markers=[
            "tapLightsPurchaseFallback(fallbackRoot,slot)",
            "waitDeviceNeutralCondition(accepted,1400,60)",
            "lights-purchase-coordinate-fallback",
            "HK_MINIGAME_TAP_ISOLATION_REV",
        ]

    for marker in recovery_markers:
        if marker not in step:
            raise SystemExit(f"lights purchase recovery contract broken: {marker}")

    shared=section("function dispatchBattleTap(element","function battleUiOverlays")
    if "battleElementFromPointIgnoringOverlays" in shared:
        raise SystemExit("lights regression: shared minigame tap still uses battle overlay filtering")
    for marker in [
        "document.elementFromPoint(x,y) || element",
        "document.elementFromPoint(px,py)",
        "HK_MINIGAME_SINGLE_TAP_REV",
    ]:
        if marker not in shared:
            raise SystemExit(f"lights shared tap contract broken: {marker}")

print("TREASURE_LIGHTS_OUTER_MODAL_CONTRACT=PASS")
