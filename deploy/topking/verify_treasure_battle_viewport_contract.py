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

if "battle-viewport-scroll-resume-20260928-r1" in s:
    tap=section("function battleElementInViewport","function dispatchBattleOverlaySafeTapAt")
    for marker in [
        "battleScrollTargetIntoViewport",
        "scrollIntoView({behavior:'auto',block:'center',inline:'center'})",
        "battle-native-offscreen-click",
        "battleElementFromPointIgnoringOverlays",
        "autoScrolled:true",
    ]:
        if marker not in tap:
            raise SystemExit(f"battle viewport contract broken: {marker}")

    # The exact battle tap must no longer refuse an off-screen connected target
    # before it has a chance to scroll it into view.
    safe=section("function dispatchBattleOverlaySafeTap(element","function dispatchBattleOverlaySafeTapAt")
    if "if (!element || !visible(element)) return false;" in safe:
        raise SystemExit("battle viewport regression: visible() still blocks off-screen targets")
    if "if (!element || !element.isConnected) return false;" not in safe:
        raise SystemExit("battle viewport contract lost connected-target guard")

    start=section("function resumePuzzleAutomation","function stop()")
    for marker in [
        "visibilitychange",
        "resumePuzzleAutomation('visibilitychange')",
        "resumePuzzleAutomation('focus')",
        "resumePuzzleAutomation('pageshow')",
        "lastSignature=''",
        "runAutoMapTick(source)",
    ]:
        if marker not in start:
            raise SystemExit(f"battle resume contract broken: {marker}")

print("TREASURE_BATTLE_VIEWPORT_CONTRACT=PASS")
