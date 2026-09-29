from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
    "// @version      1.18.95",
    "const BUILD_VERSION = '1.18.95';",
    "battle-intro-overlay-ack-20260930-r1",
    "battle-complete-exit-loop-20260930-r1",
    "chest-exhausted-exit-20260930-r1",
    "battle-open-modal-confirm-20260930-r1",
]
for marker in required:
    if marker not in s:
        raise SystemExit("1.18.95 contract missing: "+marker)

intro=s[s.find("function battleIntroModalRoot()"):s.find("function battleIntroTransitionLocked()")]
for marker in [
    "row.ack && row.ownTitle",
    "battleElementFromPointIgnoringOverlays",
    "rawBattle || battleScreenVisiblyCurrent()",
    "HK_BATTLE_INTRO_OVERLAY_ACK_REV",
]:
    if marker not in intro:
        raise SystemExit("battle intro modal contract missing: "+marker)
if "if (!battleScreenVisiblyCurrent()) return null;" in intro:
    raise SystemExit("battle intro still hard-blocked by obscured page title")

ack=s[s.find("async function runBattleIntroAcknowledge()"):s.find("async function autoMapSkipBattleWithoutFight()")]
for marker in [
    "dispatchMinigameOverlaySafeTapAt(",
    "deviceNeutralActivate(",
    "waitDeviceNeutralCondition(accepted",
    "battle-intro-ack-retry",
]:
    if marker not in ack:
        raise SystemExit("battle intro ack contract missing: "+marker)

leave=s[s.find("function autoMapPromoteActionTarget"):s.find("function autoMapModalPrimaryButton")]
for marker in [
    "function autoMapPromoteActionTarget",
    "autoMapPromoteActionTarget(shared,root)",
    "async function autoMapRecoverCompletedBattleExit",
    "dispatchMinigameOverlaySafeTapAt(",
    "сражение → подтверждаю выход 10",
    "battle-complete-exit-retry",
    "treasureGuideScreenVisible()",
]:
    if marker not in leave:
        raise SystemExit("battle completed exit contract missing: "+marker)

pre=s[s.find("if (battleRecoverFinalRewardClaimed('automap-preflight'))"):s.find("// A completed Treasury",s.find("if (battleRecoverFinalRewardClaimed('automap-preflight'))"))]
if "autoMapRecoverCompletedBattleExit('automap-activated-reward')" not in pre:
    raise SystemExit("activated victory chest does not hand off to completed-exit loop")
if "autoMapHandleExitOrContinue()" in pre:
    raise SystemExit("activated victory chest still uses generic one-shot exit")

print("BATTLE_INTRO_EXIT_LOOP_CONTRACT=PASS")
