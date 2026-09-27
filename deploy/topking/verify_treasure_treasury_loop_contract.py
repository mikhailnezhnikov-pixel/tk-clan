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

if "treasury-left-once-continuous-map-20260927-r1" in s:
    for marker in [
        "AUTO_MAP_TREASURY_LOCK_KEY",
        "function autoMapTreasuryLeftSelected()",
        "function setAutoMapTreasuryLeftSelected(",
        "function autoMapEnterTreasuryLeftPath(",
        "treasury-left-once-selected",
        "treasury-left-once-reset",
        "treasure-auto-map-next-journey",
    ]:
        if marker not in s:
            raise SystemExit(f"treasury loop contract missing: {marker}")

    choice=section("function autoMapTreasuryChoice()","function autoMapTreasuryChestRows()")
    if "if (autoMapTreasuryLeftSelected()) return null;" not in choice:
        raise SystemExit("treasury loop contract broken: route selector can re-enter another path")

    enter=section("async function autoMapEnterTreasuryLeftPath","function autoMapTreasuryChestRows()")
    for marker in [
        "setAutoMapTreasuryLeftSelected(true",
        "const ok=await autoMapTapAndConfirm(",
        "choice.element,",
        "setAutoMapTreasuryLeftSelected(false",
    ]:
        if marker not in enter:
            raise SystemExit(f"treasury one-shot entry contract broken: {marker}")

    tick=section("async function runAutoMapTick","function setAutoMapEnabled")
    done_pos=tick.find("if (autoMapTreasuryDone())")
    choice_pos=tick.find("const choice=autoMapTreasuryChoice();")
    chest_pos=tick.find("const treasuryChest=autoMapTreasuryChest();")
    if min(done_pos,choice_pos,chest_pos)<0 or not (done_pos < choice_pos < chest_pos):
        raise SystemExit("treasury priority broken: completed > choice-once > reward chest")

    if "autoMapEnterTreasuryLeftPath(choice)" not in tick:
        raise SystemExit("treasury loop contract broken: raw route click bypasses one-shot latch")

    # Returning to the map must clear the treasury one-shot latch, so the next
    # independent Treasury visit may use the left room again.
    if "setAutoMapTreasuryLeftSelected(false,{reason:'map-visible'})" not in tick:
        raise SystemExit("treasury latch is not reset on map return")

    # Completed maps must roll directly into a new map while AutoMap remains ON.
    if "setAutoMapEnabled(false,{reason:'map-complete'" in tick:
        raise SystemExit("continuous-map contract broken: AutoMap still stops at map completion")
    for marker in [
        "autoMapStatus('новая карта'",
        "setAutoMapSessionStarted(false)",
        "autoMapStartJourney('next-journey')",
    ]:
        if marker not in tick:
            raise SystemExit(f"continuous-map contract broken: {marker}")

    helper=section("async function autoMapStartJourney","async function runAutoMapTick")
    for marker in [
        "setAutoMapStartLock(Date.now())",
        "autoMapTapAndConfirm(journey,label,1)",
        "setAutoMapSessionStarted(true)",
        "setAutoMapStartLock(0)",
    ]:
        if marker not in helper:
            raise SystemExit(f"journey restart contract broken: {marker}")

print("TREASURE_TREASURY_LOOP_CONTRACT=PASS")
