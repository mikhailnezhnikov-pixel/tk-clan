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

# Starting/resuming AutoMap with an already-open lamp purchase modal is a
# permanent regression scenario. The invariant is behavioral:
#   1) identify a dismissible OUTER lamp dialog,
#   2) close it without spending,
#   3) continue from the actual 3x3 board.
# The implementation may evolve from the generic centered helper to a dedicated
# outer-dialog resolver, so the contract deliberately accepts both generations.
if "treasure-lights-resume-open-modal-20260927-r1" in s:
    root=section("function lightsModalRoot()","async function waitLightsModal")
    stale=section("async function clearStaleLightsModalBeforeStep","async function runLightsModalStep")

    if "treasure-lights-outer-modal-20260927-r1" in s:
        for marker in [
            "lightsOuterModalRoot()",
            "if (outer) return outer;",
        ]:
            if marker not in root:
                raise SystemExit(f"lights resume contract broken in dedicated modal root: {marker}")

        for marker in [
            "lightsOuterModalRoot()",
            "autoMapModalCloseButton",
            "lights-clear-stale-outer-close",
            "lights-clear-stale-outer-corner",
        ]:
            if marker not in stale:
                raise SystemExit(f"lights resume contract broken in dedicated stale-modal drain: {marker}")
    else:
        for marker in [
            "treasureCenteredModalRoot()",
            "centeredText",
            "return centered;",
        ]:
            if marker not in root:
                raise SystemExit(f"lights resume contract broken in legacy modal root: {marker}")

        for marker in [
            "treasureCenteredModalRoot()",
            "autoMapModalCloseButton",
            "lights-clear-stale-outer-close",
            "lights-clear-stale-outer-corner",
        ]:
            if marker not in stale:
                raise SystemExit(f"lights resume contract broken in legacy stale-modal drain: {marker}")

    # Never confirm cost while draining a modal that predates the current step.
    forbidden=[
        "lightsPurchaseButton(",
        "tapLightsPurchaseFallback(",
        "lights-confirm-cost",
    ]
    for marker in forbidden:
        if marker in stale:
            raise SystemExit(f"lights resume contract spends while draining stale modal: {marker}")

    fail=section("function failLightsAuto","async function runLightsAuto")
    fatal=fail[fail.find("const fatalReasons"):fail.find("if (autoMapOwnsLights")]
    for recoverable in ["stale-modal-blocking","modal-not-closed-after-change"]:
        if recoverable in fatal:
            raise SystemExit(f"lights resume contract made UI recovery fatal: {recoverable}")

print("TREASURE_LIGHTS_RESUME_CONTRACT=PASS")
