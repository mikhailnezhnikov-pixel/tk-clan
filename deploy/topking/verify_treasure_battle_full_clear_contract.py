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

if "battle-automap-full-clear-20260927-r1" in s:
    run_battle=section("function runBattle()","// ----- Full Treasure Map orchestrator -----")
    if "battle-auto-skip-owned-by-map" in run_battle:
        raise SystemExit("battle contract broken: runBattle still skips fights under AutoMap")
    for marker in [
        "const solution = solveBattle(state,maxAttack);",
        "void runBattleAuto(solution);",
    ]:
        if marker not in run_battle:
            raise SystemExit(f"battle contract broken in runBattle: {marker}")

    owner=section("function autoMapEnsureOwnedModule","function autoMapBlockOwnedModule")
    for marker in [
        "sig.startsWith('BATTLE|')",
        "name='battle'",
        "enabled=battleAutoEnabled",
        "setBattleAutoEnabled(true)",
    ]:
        if marker not in owner:
            raise SystemExit(f"battle ownership contract broken: {marker}")

    tick=section("async function runAutoMapTick","function setAutoMapEnabled")
    pos=tick.find("if (signature.startsWith('BATTLE')) {")
    if pos<0:
        raise SystemExit("battle contract broken: AutoMap BATTLE branch missing")
    battle=tick[pos:tick.find("if (signature.startsWith('FISHING|'))",pos)]
    if "setTimeout(checkPuzzle,20)" not in battle:
        raise SystemExit("battle contract broken: AutoMap must dispatch battle solver")
    for forbidden in [
        "autoMapSkipBattleWithoutFight()",
        "battle-auto-cancel-for-skip",
    ]:
        if forbidden in battle:
            raise SystemExit(f"battle contract regressed to skip: {forbidden}")

    check=section("function checkPuzzle()","function start()")
    is_battle=check[check.find("if (isBattle) {"):check.find("if (isBattleReward",check.find("if (isBattle) {"))]
    if "runBattle();" not in is_battle:
        raise SystemExit("battle contract broken: checkPuzzle must dispatch runBattle")

if "battle-strict-exit-gate-20260927-r1" in s:
    gate=section("function battleExitState()","function battleLeaveBackButton")
    for marker in [
        "battleVictoryElement()",
        "battleVictoryModalRoot()",
        "Number(enemy.hp)<=swords",
        "reason:'attack-available'",
        "reason:'no-attack-available'",
    ]:
        if marker not in gate:
            raise SystemExit(f"strict battle exit gate broken: {marker}")

    run_battle=section("function runBattle()","// ----- Full Treasure Map orchestrator -----")
    if "insufficientByHp" in run_battle or "insufficientBySolver" in run_battle:
        raise SystemExit("strict battle exit gate broken: full-clear heuristics still trigger exit")
    for marker in [
        "if (!solution || solution.order.length===0)",
        "void runBattleInsufficientExit({",
        "reason:'no-legal-attack'",
    ]:
        if marker not in run_battle:
            raise SystemExit(f"strict battle run logic missing: {marker}")

    insufficient=section("async function runBattleInsufficientExit","function addNumber")
    for marker in [
        "let gate=battleExitState();",
        "if (!gate.allowed)",
        "battle-insufficient-exit-blocked",
    ]:
        if marker not in insufficient:
            raise SystemExit(f"strict battle insufficient-exit guard missing: {marker}")

    recover=section("async function autoMapRecoverOpenLeaveModal","function autoMapModalPrimaryButton")
    for marker in [
        "const battleGate=battleExitState();",
        "battleLeaveBackButton(modal)",
        "battle-leave-modal-blocked",
    ]:
        if marker not in recover:
            raise SystemExit(f"strict battle leave-modal recovery missing: {marker}")

    tap=section("async function autoMapTapAndConfirm","async function autoMapDismissReward")
    for marker in [
        "battle-exit-guard",
        "battleExitState()",
    ]:
        if marker not in tap:
            raise SystemExit(f"strict battle generic-exit guard missing: {marker}")

if "battle-raw-context-mobile-tap-20260927-r1" in s:
    gate=section("function battleExitState()","function battleLeaveBackButton")
    if "const enemies=board.filter(enemy=>enemy!==null);" not in gate:
        raise SystemExit("raw battle context contract broken: covered enemies must still count")

    recover=section("async function autoMapRecoverOpenLeaveModal","function autoMapModalPrimaryButton")
    if "battleLeaveBackButton(modal) || autoMapModalCloseButton(modal)" not in recover:
        raise SystemExit("raw battle context contract broken: premature leave modal needs close fallback")

    runner=section("async function runBattleAuto","async function runBattleInsufficientExit")
    for marker in [
        "dispatchBattleTap(element,'battle-open-card')",
        "dispatchBattleTap(actionButton,'battle-confirm-attack')",
    ]:
        if marker not in runner:
            raise SystemExit(f"battle mobile tap contract broken: {marker}")
    for forbidden in [
        "element.click();",
        "actionButton.click();",
    ]:
        if forbidden in runner:
            raise SystemExit(f"battle mobile tap regressed to raw click: {forbidden}")

print("TREASURE_BATTLE_FULL_CLEAR_CONTRACT=PASS")
