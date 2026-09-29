from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
  "// @version      1.18.92",
  "treasure-map-target-scroll-20260929-r1",
  "treasure-exit-confirm-retry-20260929-r1",
  "battle-modal-action-recovery-20260929-r1",
  "treasure-key-purchase-activation-20260929-r1",
  "function battleEnemyModalActionButton(expectedCost)",
  "function autoMapPrepareMapTarget(element,label='map-target')",
  "treasure-key-purchase-activation-retry",
  "exit-confirm-retry",
]
for marker in required:
    if marker not in s:
        raise SystemExit("treasure recovery contract broken: "+marker)

# Open fighter modal gets a first-class action lookup before generic scoring.
start=s.find("function battleActionButton(expectedCost)")
end=s.find("function waitBattleActionButton",start)
battle=s[start:end]
if "const modalAction=battleEnemyModalActionButton(expectedCost);" not in battle:
    raise SystemExit("battle modal action does not outrank generic action scoring")
if "if (modalAction) return modalAction;" not in battle:
    raise SystemExit("battle modal action recovery not returned directly")

# Key purchase is verified by actual receipt/modal/state change.
start=s.find("async function autoMapBuyTreasureKeyIfPresent()")
end=s.find("async function autoMapWaitModal",start)
key=s[start:end]
for marker in [
    "const purchaseAccepted=()=>",
    "deviceNeutralActivate(",
    "dispatchMinigameOverlaySafeTapAt(",
    "waitDeviceNeutralCondition(purchaseAccepted",
]:
    if marker not in key:
        raise SystemExit("key purchase activation missing: "+marker)
if "if (!dispatchAutoMapTap(target.element,'treasure-key-buy-'" in key:
    raise SystemExit("raw key purchase click remains authoritative")

# Route cell must be scrolled into view before coordinate activation.
start=s.find("async function autoMapPrepareMapTarget")
end=s.find("async function autoMapTapAndConfirm",start)
prep=s[start:end]
for marker in [
    "scrollIntoView",
    "battleElementFromPointIgnoringOverlays",
    "treasure-map-target-prepared",
]:
    if marker not in prep:
        raise SystemExit("map target preparation missing: "+marker)

tap=s[s.find("async function autoMapTapAndConfirm"):s.find("async function autoMapDismissReward")]
if "await autoMapPrepareMapTarget(element,label)" not in tap:
    raise SystemExit("map target scroll not called before tap")
if "dispatchMinigameOverlaySafeTapAt(" not in tap:
    raise SystemExit("map target does not use overlay-safe coordinate tap")

# Leave/exit confirmations use verified device-neutral activation and retry.
for section_start,section_end in [
    ("async function autoMapTapAndConfirm","async function autoMapDismissReward"),
    ("async function autoMapRecoverOpenLeaveModal","async function autoMapSkipBattleWithoutFight"),
]:
    a=s.find(section_start)
    b=s.find(section_end,a)
    if a<0 or b<0:
        raise SystemExit("missing exit section: "+section_start)
    block=s[a:b]
    for marker in ["deviceNeutralActivate(","dispatchMinigameOverlaySafeTapAt(","HK_EXIT_CONFIRM_RETRY_REV"]:
        if marker not in block:
            raise SystemExit("exit recovery missing in "+section_start+": "+marker)

# Keep the previous fixes intact.
for marker in [
  "battle-context-foreground-20260929-r1",
  "treasure-key-receipt-priority-20260929-r1",
  "treasury-corridor-ack-20260929-r1",
  "treasure-map-dominates-stale-minigame-20260929-r1",
  "automation-toggle-trusted-input-20260929-r1",
  "coordinate-overlay-guard-20260929-r1",
  "treasure-map-quiet-gate-20260929-r1",
  "chest-lot-hard-gate-20260929-r1",
  "battle-offscreen-action-scroll-20260929-r1",
]:
    if marker not in s:
        raise SystemExit("preserved behavior missing: "+marker)

print("TREASURE_RECOVERY_CONTRACT=PASS")
