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
        raise SystemExit("battle full-clear contract broken: runBattle still skips all fights under AutoMap")
    for marker in [
        "const solution = solveBattle(state,maxAttack);",
        "const insufficientByHp=totalHp>maxAttack;",
        "const insufficientBySolver=solverKilled<enemies.length;",
        "void runBattleInsufficientExit({",
        "void runBattleAuto(solution);",
    ]:
        if marker not in run_battle:
            raise SystemExit(f"battle full-clear contract broken in runBattle: {marker}")

    owner=section("function autoMapEnsureOwnedModule","function autoMapBlockOwnedModule")
    for marker in [
        "sig.startsWith('BATTLE|')",
        "sig.startsWith('BATTLE_REWARD')",
        "name='battle'",
        "enabled=battleAutoEnabled",
        "setBattleAutoEnabled(true)",
    ]:
        if marker not in owner:
            raise SystemExit(f"battle ownership contract broken: {marker}")

    tick=section("async function runAutoMapTick","function setAutoMapEnabled")
    battle_anchor="if (signature.startsWith('BATTLE')) {"
    pos=tick.find(battle_anchor)
    if pos<0:
        raise SystemExit("battle full-clear contract broken: AutoMap BATTLE branch missing")
    battle=tick[pos:tick.find("if (signature.startsWith('FISHING|'))",pos)]
    for marker in [
        "autoMapStatus('сражение'",
        "setTimeout(checkPuzzle,20)",
    ]:
        if marker not in battle:
            raise SystemExit(f"battle full-clear AutoMap branch broken: {marker}")
    for forbidden in [
        "autoMapSkipBattleWithoutFight()",
        "battle-auto-cancel-for-skip",
    ]:
        if forbidden in battle:
            raise SystemExit(f"battle full-clear AutoMap branch regressed to skip: {forbidden}")

    check=section("function checkPuzzle()","function start()")
    is_battle=check[check.find("if (isBattle) {"):check.find("if (isBattleReward",check.find("if (isBattle) {"))]
    if "runBattle();" not in is_battle:
        raise SystemExit("battle full-clear contract broken: checkPuzzle must dispatch runBattle")
    for forbidden in [
        "battle-skip-dispatch",
        "battle-skip-check-puzzle",
    ]:
        if forbidden in is_battle:
            raise SystemExit(f"battle check regressed to skip: {forbidden}")

    insufficient=section("async function runBattleInsufficientExit","function addNumber")
    for marker in [
        "autoMapTapAndConfirm(exit,'battle-insufficient-swords-exit'",
        "battle-full-clear-exit-complete",
    ]:
        if marker not in insufficient:
            raise SystemExit(f"battle insufficient-swords exit contract broken: {marker}")

print("TREASURE_BATTLE_FULL_CLEAR_CONTRACT=PASS")
