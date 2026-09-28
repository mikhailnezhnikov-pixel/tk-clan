from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
  "// @version      1.18.80",
  "battle-target-safe-scroll-20260928-r1",
  "function battlePointBelongsToElement",
  "function battleElementTapProbe",
  "function battleTargetSafeBand",
  "async function battleScrollTargetIntoViewportAsync",
  "element.scrollIntoView({behavior:'auto',block:'center',inline:'nearest'})",
  "window.scrollBy({top:center-desired,left:0,behavior:'auto'})",
  "blockerText:probe.leafText||''",
  "await battleScrollTargetIntoViewportAsync(",
  "reason:'target-not-safe-after-scroll'",
  "verifiedTarget:true",
  "battleTargetScrollRevision:HK_BATTLE_TARGET_SCROLL_REV",
]
for marker in required:
    if marker not in s:
        raise SystemExit("battle safe-scroll contract broken: "+marker)

for forbidden in [
  "battle-native-offscreen-click",
  "battleScrollTargetIntoViewport(element,label);",
]:
    if forbidden in s:
        raise SystemExit("unsafe/synchronous battle target handling remains: "+forbidden)

# The previously fixed full-map solver and one-berry egg behavior must survive.
for marker in [
  "battle-full-fair-state-20260928-r1",
  "battle-egg-one-berry-buy-20260928-r1",
  "fairState('fair_mini_game_fight',playerDocument)",
  "function battleEggOfferTarget()",
  "battle-overlay-safe-targeting-20260928-r1",
  "battle-reward-state-machine-20260928-r1",
  "battle-strict-exit-gate-20260927-r1",
  "chest-visible-claim-priority-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("preserved battle/map behavior missing: "+marker)

print("BATTLE_SAFE_SCROLL_CONTRACT=PASS")
