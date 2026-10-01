from pathlib import Path
import sys

s=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js").read_text(encoding="utf-8")

def part(a,b):
    i=s.find(a)
    if i<0: raise SystemExit("missing section "+a)
    j=s.find(b,i+len(a))
    if j<0: raise SystemExit("missing section end "+b)
    return s[i:j]

current_version="1.18.100" if "battle-single-tap-until-receipt-20261001-r1" in s else "1.18.99"
for marker in [
    "// @version      "+current_version,
    "const BUILD_VERSION = '"+current_version+"';",
    "battle-no-premature-exit-20261001-r1",
    "battle-attack-state-receipt-20261001-r1",
    "treasury-intro-mobile-ack-20261001-r1",
    "treasury-battle-foreground-handoff-20261001-r1",
    "leave-modal-foreground-truth-20261001-r1",
    "trader-map-modal-approval-20260930-r1"
]:
    if marker not in s: raise SystemExit("missing revision "+marker)

gate=part("function battleExitState()","function battleLeaveBackButton(")
ordered=[
    "if (enemyModalPending)",
    "if (!Number.isFinite(swords))",
    "const attackable=enemies.filter(enemy=>Number(enemy.hp)>0 && Number(enemy.hp)<=swords)",
    "if (attackable.length>0)",
    "if (eggOffer)",
    "if (rewardPending)",
    "const activatedSettled=battleRecoverFinalRewardClaimed('exit-state')",
    "if (battleFinalRewardClaimed)",
    "reason:'no-attack-available'",
]
indices=[gate.find(marker) for marker in ordered]
# The early affordable-enemy branch deliberately checks and clears a stale
# claim. The final reward-claimed allowance is the LAST occurrence.
indices[-2]=gate.rfind("if (battleFinalRewardClaimed)")
if min(indices)<0 or indices!=sorted(indices):
    raise SystemExit("exit gate can still permit exit ahead of affordable enemies/modal")
if "battleFinalRewardClaimed=false" not in gate:
    raise SystemExit("stale completion flag not invalidated")

board=part("function getBattleBoard()","function battleEggOfferCost(")
for marker in ["const currentFairSlots=battleFairSlots();","if (fairEnemies>0 || currentFairSlots.length>0)"]:
    if marker not in board: raise SystemExit("stale enemy DOM fallback: "+marker)

recovered=part("function battleRecoverFinalRewardClaimed(","function battleVictoryElement()")
if recovered.find("if (enemyModalPending ||")<0 or recovered.find("if (enemyModalPending ||")>recovered.find("battleFinalRewardSettled()"):
    raise SystemExit("reward recovered ahead of live enemy")

sig=part("function getSignature()","function checkPuzzle()")
if not (0<=sig.find("const liveBattleModal=battleEnemyModalRoot();")<sig.find("battleRecoverFinalRewardClaimed('signature')")):
    raise SystemExit("live battle must outrank old Activated chest")

confirm=part("async function battleConfirmAlreadyOpenEnemyModal(","const battleOpenModalStall=")
for marker in [
    "while (Date.now()-elapsed<2200)",
    "reason:'price-loading-or-disabled'",
    "const beforeBoard=getBattleBoard().filter(Boolean)",
    "const swordSpent=",
    "const enemyStateChanged=",
    "const rewardArrived=",
    "swordSpent || enemyStateChanged || (rewardArrived && !battleEnemyModalRoot())",
    "reason:'no-server-state-change'",
]:
    if marker not in confirm: raise SystemExit("attack receipt missing "+marker)
if "currentRoot!==root" in confirm or "currentSignature!==before" in confirm:
    raise SystemExit("modal redraw/signature change can falsely confirm attack")

stall=part("const battleOpenModalStall=","async function runBattleOpenEnemyModalRecovery(")
for marker in [
    "now-battleOpenModalStall.since<15000",
    "battleOpenModalStall.retries>=2",
    "battle-stalled-modal-close",
    "battleInsufficientExitNotBefore=Date.now()+2500",
    "battle-modal-stall-recovery-exhausted",
]:
    if marker not in stall: raise SystemExit("bounded stalled modal recovery missing "+marker)

if "battleRecoverStalledEnemyModal(result.reason)" not in s:
    raise SystemExit("stalled modal recovery not wired")

complete=part("async function autoMapRecoverCompletedBattleExit(","function autoMapModalPrimaryButton(")
for marker in [
    "const initialGate=battleExitState();",
    "const attemptGate=battleExitState();",
    "const preConfirmGate=battleExitState();",
    "battle-exit-cancel-before-10",
    "autoMapRecoverOpenLeaveModal('battle-exit-guard-before-10')"
]:
    if marker not in complete: raise SystemExit("completed battle exit unsafe "+marker)

generic=part("async function autoMapTapAndConfirm(","async function autoMapDismissReward()")
for marker in ["const beforeTapGate=battleExitState();","const beforePayGate=battleExitState();"]:
    if marker not in generic: raise SystemExit("generic exit check missing "+marker)

recover=part("async function autoMapRecoverOpenLeaveModal(","async function autoMapRecoverCompletedBattleExit(")
if "const paidExitGate=battleExitState();" not in recover:
    raise SystemExit("recovered leave modal could pay 10 after board changed")

runner=part("function runBattle()","// ----- Full Treasure Map orchestrator")
if "battle-stale-reward-cleared-before-attack" not in runner:
    raise SystemExit("new battle not released from previous claim")

print("BATTLE_STATE_RECEIPT_CONTRACT=PASS")
