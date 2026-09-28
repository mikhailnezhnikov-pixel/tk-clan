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



# 1.18.63+: lamp presses are a strict transaction and leaving the labyrinth is
# forbidden until the final reward is actually claimed and acknowledged.
if "lights-confirm-ack-before-board-reward-gate-20260928-r1" in s:
    board=section("function getLightsBoard()","function lightNeighbours(position)")
    step=section("async function runLightsModalStep","function lightsRewardElement()")
    completed=section("function lightsRoomCompleted()","function lightsRewardModalRoot()")
    exit_flow=section("async function autoMapReturnFromCompletedLights()","function autoMapBottomContinueButton")

    for marker in [
        "candidatesBySlot",
        "intersectsViewport",
        "lights-board-responsive-duplicates-filtered",
    ]:
        if marker not in board:
            raise SystemExit(f"lights confirmed-state contract lost visible-board selection: {marker}")

    for marker in [
        "lights-confirm-ack-",
        "state:'ack_confirmed'",
        "state:'board_changed'",
        "waitLightsAcknowledge(runId,before",
        "waitLightsBoardChange(before,runId",
    ]:
        if marker not in step:
            raise SystemExit(f"lights confirmed-state contract lost transaction stage: {marker}")

    ack_pos=step.find("lights-confirm-ack-")
    board_wait_pos=step.find("waitLightsBoardChange(before,runId")
    if ack_pos < 0 or board_wait_pos < 0 or ack_pos > board_wait_pos:
        raise SystemExit("lights confirmed-state contract waits for board before acknowledgement")

    if "return lightsFinalRewardClaimed===true;" not in completed:
        raise SystemExit("lights reward contract allows Activated to masquerade as claimed")
    if "lightsRewardActivated()" in completed:
        raise SystemExit("lights reward contract still treats Activated as completed")

    for marker in [
        "HK_REWARD_CLAIM_BEFORE_EXIT_REV",
        "lights-exit-blocked-final-reward",
        "lights-exit-blocked-reward-confirmation",
        "if (!lightsFinalRewardClaimed)",
        "lightsRewardModalRoot() || lightsRewardAckButton()",
    ]:
        if marker not in exit_flow:
            raise SystemExit(f"lights reward-before-exit contract broken: {marker}")

    unsafe_recovery=[
        "source:'activated-reward-dom'",
        "lightsFinalRewardClaimed=true",
    ]
    prefix=exit_flow[:exit_flow.find("autoMapStatus('выход за 10'")]
    for marker in unsafe_recovery:
        if marker in prefix:
            raise SystemExit(f"lights reward-before-exit contract has unsafe recovery: {marker}")

print("TREASURE_LIGHTS_RESUME_CONTRACT=PASS")
