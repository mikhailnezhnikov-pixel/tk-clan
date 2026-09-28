from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
  "// @version      1.18.82",
  "battle-visible-point-truth-20260929-r1",
  "function battleTargetSafeBand(element)",
  "return !!probe.ready;",
  "const initialProbe=battleElementTapProbe(element);",
  "if (initialProbe.ready)",
  "if (!probe.ready) {",
  "const success=!!probe.ready;",
  "reason:'target-not-clickable-after-scroll'",
  "battleVisiblePointTruthRevision:HK_BATTLE_VISIBLE_POINT_TRUTH_REV",
]
for marker in required:
    if marker not in s:
        raise SystemExit("battle visible-point contract broken: "+marker)

for forbidden in [
  "window.innerHeight*0.68",
  "cy>=top && cy<=Math.max(top+40,bottom)",
  "!targetProbe.ready || !battleTargetSafeBand(element)",
  "!probe.ready || !battleTargetSafeBand(element)",
]:
    if forbidden in s:
        raise SystemExit("lower-row viewport gate still present: "+forbidden)

for marker in [
  "battle-target-safe-scroll-20260928-r1",
  "battle-full-fair-state-20260928-r1",
  "battle-egg-one-berry-buy-20260928-r1",
  "battle-overlay-safe-targeting-20260928-r1",
  "battle-reward-state-machine-20260928-r1",
  "battle-strict-exit-gate-20260927-r1",
  "clan-crest-launcher-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("preserved behavior missing: "+marker)

print("BATTLE_VISIBLE_POINT_TRUTH_CONTRACT=PASS")
