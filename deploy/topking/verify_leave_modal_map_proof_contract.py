from pathlib import Path
import sys

s=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js").read_text(encoding="utf-8")
for marker in [
    "// @version      1.18.97",
    "const BUILD_VERSION = '1.18.97';",
    "leave-modal-foreground-truth-20261001-r1",
    "exit-map-proof-20261001-r1",
    "battle-open-modal-priority-20260930-r1",
    "trader-map-modal-approval-20260930-r1",
    "battle-intro-overlay-ack-20260930-r1",
]:
    if marker not in s: raise SystemExit("1.18.97 missing: "+marker)

def section(start,end):
    a=s.find(start)
    if a<0: raise SystemExit("missing section: "+start)
    b=s.find(end,a+len(start))
    if b<0: raise SystemExit("missing end: "+end)
    return s[a:b]

modal=section("function autoMapReturnMapConfirmed()","function autoMapPromoteActionTarget")
for marker in [
    "function autoMapReturnMapConfirmed()",
    "autoMapMapIsForeground()",
    "autoMapElementIsForeground(journey)",
    "function autoMapLeaveModalRoot()",
    "if (!price) return null;",
    "if (!explicit && !hasPrompt && !hasBack) return null;",
    "battleElementFromPointIgnoringOverlays(cx,cy,null)",
    "rect.width>vw*0.94",
    r"/^(?:10|10\s*(?:ягод(?:ы)?|berries|berry))$/i",
]:
    if marker not in modal: raise SystemExit("modal truth contract missing: "+marker)
if r"/Продолжить\?|Continue\?|10|Назад|Back/i.test(row.text)" in modal:
    raise SystemExit("substring 10 still permits ghost leave modal")

recovery=section("async function autoMapRecoverOpenLeaveModal","async function autoMapRecoverCompletedBattleExit")
for marker in [
    "if (autoMapReturnMapConfirmed())",
    "result:'map-foreground-confirmed'",
    "leave-modal-return-not-confirmed",
    "setTimeout(()=>void runAutoMapTick('leave-modal-still-in-room'),900);",
]:
    if marker not in recovery: raise SystemExit("leave recovery contract missing: "+marker)
if "if (treasureGuideScreenVisible() || autoMapStateFingerprint()!==before)" in recovery:
    raise SystemExit("phantom fingerprint-based leave success regressed")

completed=section("async function autoMapRecoverCompletedBattleExit","function autoMapModalPrimaryButton")
if "const roomGone=()=>autoMapReturnMapConfirmed();" not in completed:
    raise SystemExit("completed battle exit does not verify real map")

generic=section("async function autoMapTapAndConfirm","async function autoMapDismissReward")
for marker in [
    "? autoMapLeaveModalRoot()",
    "? autoMapLeaveConfirmButton(modal,10)",
    "autoMapReturnMapConfirmed()",
    "mode:'map-confirmed'",
]:
    if marker not in generic: raise SystemExit("generic exit safety missing: "+marker)

print("LEAVE_MODAL_MAP_PROOF_CONTRACT=PASS")
