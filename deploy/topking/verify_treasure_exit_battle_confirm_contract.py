from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
    "// @version      1.18.94",
    "const BUILD_VERSION = '1.18.94';",
    "chest-exhausted-exit-20260930-r1",
    "battle-open-modal-confirm-20260930-r1",
    "function battleEnemyModalRoot()",
    "async function battleConfirmAlreadyOpenEnemyModal",
]
for marker in required:
    if marker not in s:
        raise SystemExit("1.18.94 contract missing: "+marker)

work=s[s.find("function treasureChestWorkState()"):s.find("function treasureChestTarget()")]
for marker in [
    "reason:'no-affordable-chest-or-key'",
    "exhausted:true",
    "exhaustedChestCount:chestRows.length",
    "phase:'done'",
]:
    if marker not in work:
        raise SystemExit("chest exhausted-state contract missing: "+marker)
if "pending:chestRows.length" in work[work.find("reason:'no-affordable-chest-or-key'")-500:work.find("reason:'no-affordable-chest-or-key'")+500]:
    raise SystemExit("unaffordable chest still blocks room completion")

auto_start=s.rfind("if (signature.startsWith('CHESTS|')) {")
auto_end=s.find("// Between rooms",auto_start)
auto=s[auto_start:auto_end]
for marker in [
    "treasure-chest-exhausted-exit",
    "autoMapStatus('сундуки → выход'",
    "autoMapHandleExitOrContinue()",
    "chest-exhausted-exit-retry",
]:
    if marker not in auto:
        raise SystemExit("chest exit handoff missing: "+marker)

modal=s[s.find("function battleEnemyModalActionButton(expectedCost)"):s.find("function battleActionButton(expectedCost)")]
if "battleScreenVisiblyCurrent()" in modal:
    raise SystemExit("battle action modal still depends on obscured page title")
if "МОЖНО\\s+ОТЫСКАТЬ|CAN\\s+BE\\s+FOUND" not in modal:
    raise SystemExit("battle modal lacks strong semantic root")

runner=s[s.find("async function runBattleAuto(solution)"):s.find("async function runBattleInsufficientExit",s.find("async function runBattleAuto(solution)"))]
for marker in [
    "battleConfirmAlreadyOpenEnemyModal(expectedCost,runId)",
    "source:'already-open-modal'",
    "battleConfirmAlreadyOpenEnemyModal(expectedCost,runId,before)",
    "source:'opened-modal'",
]:
    if marker not in runner:
        raise SystemExit("battle runner open-modal recovery missing: "+marker)

helper=s[s.find("async function battleConfirmAlreadyOpenEnemyModal"):s.find("function battleActionButton(expectedCost)")]
for marker in [
    "dispatchBattleOverlaySafeTap(action,'battle-open-modal-confirm')",
    "dispatchBattleOverlaySafeTapAt(",
    "currentRoot!==root",
    "currentSignature!==before",
    "currentSwords!==beforeSwords",
]:
    if marker not in helper:
        raise SystemExit("battle modal confirmation receipt missing: "+marker)

print("TREASURE_EXIT_BATTLE_CONFIRM_CONTRACT=PASS")
