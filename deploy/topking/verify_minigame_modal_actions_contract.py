from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
  "// @version      1.18.87",
  "minigame-overlay-pass-through-20260929-r1",
  "battle-action-modal-div-20260929-r1",
  "function battleActionButton(expectedCost)",
  "button,[role=\"button\"],a,[onclick],div,span",
  "dispatchBattleOverlaySafeTap(ack,'lights-clear-stale-ack-'+slot)",
  "dispatchMinigameOverlaySafeTapAt(",
  "function waitBattleActionButton(expectedCost,runId,timeoutMs=4200)",
  "battle-action-button-found",
]
for marker in required:
    if marker not in s:
        raise SystemExit("minigame modal actions contract broken: "+marker)

# Preserve the shared dispatcher contract; Lights-specific recovery must use
# overlay-safe paths without changing generic minigame semantics.
start=s.find("function dispatchBattleTap(element")
end=s.find("function battleUiOverlays()",start)
block=s[start:end]
for marker in [
    "document.elementFromPoint(x,y) || element",
    "document.elementFromPoint(px,py)",
]:
    if marker not in block:
        raise SystemExit("shared tap contract changed unexpectedly: "+marker)

lights_start=s.find("async function clearStaleLightsModalBeforeStep")
lights_end=s.find("function lightsRewardElement()",lights_start)
lights=s[lights_start:lights_end]
for marker in [
    "dispatchBattleOverlaySafeTap(ack,'lights-clear-stale-ack-'+slot)",
    "dispatchBattleOverlaySafeTap(close,'lights-clear-stale-close-'+slot)",
    "dispatchBattleOverlaySafeTap(ackButton,'lights-confirm-ack-fallback-'+slot)",
    "dispatchMinigameOverlaySafeTapAt(",
]:
    if marker not in s:
        raise SystemExit("lights overlay-safe recovery missing: "+marker)

# Battle action search must include non-semantic game controls while rejecting
# huge modal containers and close/ack controls.
start=s.find("function battleActionButton(expectedCost)")
end=s.find("function waitBattleActionButton",start)
block=s[start:end]
for marker in [
    "[onclick],div,span",
    "area>viewportArea*0.22",
    "text.length>120",
    "понятно|got it|understood",
    "row.score>=240",
]:
    if marker not in block:
        raise SystemExit("battle action selector guard missing: "+marker)

for marker in [
  "battle-preview-resume-20260929-r1",
  "battle-intro-hard-gate-20260929-r1",
  "battle-visible-point-truth-20260929-r1",
  "battle-full-fair-state-20260928-r1",
  "battle-egg-one-berry-buy-20260928-r1",
  "lights-confirm-ack-before-board-reward-gate-20260928-r1",
  "treasure-automap-module-ownership-20260927-r1",
  "clan-crest-transparent-mask-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("preserved behavior missing: "+marker)

print("MINIGAME_MODAL_ACTIONS_CONTRACT=PASS")
