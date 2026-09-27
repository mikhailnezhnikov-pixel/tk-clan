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

print("TREASURE_LIGHTS_OUTER_MODAL_CONTRACT=PASS")
