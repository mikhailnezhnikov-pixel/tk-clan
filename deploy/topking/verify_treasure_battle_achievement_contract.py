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

if "battle-achievement-priority-20260927-r1" in s:
    core=section("function battleAchievementStorageKey()","function runBattle()")
    if "hk:treasure:battle-achievements:v1" not in s:
        raise SystemExit("battle achievement storage key missing")
    for marker in [
        "function battleAchievementRemoteComplete(",
        "function battleAchievementDone(",
        "function battleAchievementMark(",
        "function battleAchievementObserveState(",
        "function solveBattleAchievement(",
        "function battleAchievementPlan(",
        "kind==='hp16'",
        "kind==='total68'",
        "maxHp>=16",
        "totalHp>=68",
        "enemy.type!==GREEN && enemy.type!==BLUE",
        "visited<6000",
        "maxDepth=8",
    ]:
        if marker not in core:
            raise SystemExit(f"battle achievement contract broken: {marker}")

    # One-time state must be account scoped and server/DOM completion aware.
    for marker in [
        "licenseState.playerId",
        "playerIdentity(playerDocument?.player || {})",
        "localStorage.getItem(battleAchievementStorageKey())",
        "localStorage.setItem(battleAchievementStorageKey()",
        "achiev|достиж",
        "completed|claimed|done|unlocked",
    ]:
        if marker not in core:
            raise SystemExit(f"battle achievement completion contract broken: {marker}")

    run=section("function runBattle()","// ----- Full Treasure Map orchestrator -----")
    for marker in [
        "battleAchievementObserveState(state);",
        "let solution=battleAchievementPlan(state,maxAttack);",
        "if (!solution) solution=solveBattle(state,maxAttack);",
        "solution.mode||'normal'",
    ]:
        if marker not in run:
            raise SystemExit(f"battle achievement run integration broken: {marker}")

    auto=section("async function runBattleAuto","async function runBattleInsufficientExit")
    if "mode:String(solution.mode||'normal')" not in auto:
        raise SystemExit("battle achievement mode is not carried into auto diagnostics")

    # Achievement planning must not weaken the strict leave gate or mobile tap path.
    strict=section("function battleExitState()","function battleLeaveBackButton")
    for marker in [
        "const enemies=board.filter(enemy=>enemy!==null);",
        "reason:'attack-available'",
        "reason:'no-attack-available'",
    ]:
        if marker not in strict:
            raise SystemExit(f"achievement patch weakened battle exit gate: {marker}")

    auto=section("async function runBattleAuto","async function runBattleInsufficientExit")
    if "minigame-tap-isolation-lights-recovery-20260928-r1" in s:
        required_taps=[
            "dispatchBattleOverlaySafeTap(element,'battle-open-card')",
            "dispatchBattleOverlaySafeTap(actionButton,'battle-confirm-attack')",
        ]
    else:
        required_taps=[
            "dispatchBattleTap(element,'battle-open-card')",
            "dispatchBattleTap(actionButton,'battle-confirm-attack')",
        ]
    for marker in required_taps:
        if marker not in auto:
            raise SystemExit(f"achievement patch weakened mobile battle tap: {marker}")

print("TREASURE_BATTLE_ACHIEVEMENT_CONTRACT=PASS")
