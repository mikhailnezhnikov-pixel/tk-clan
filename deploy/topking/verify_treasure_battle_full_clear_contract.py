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
    required=["void runBattleAuto(solution);"]
    if "battle-achievement-priority-20260927-r1" in s:
        required += [
            "let solution=battleAchievementPlan(state,maxAttack);",
            "if (!solution) solution=solveBattle(state,maxAttack);",
        ]
    else:
        required += ["const solution = solveBattle(state,maxAttack);"]
    for marker in required:
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
        if marker not in runner:
            raise SystemExit(f"battle mobile tap contract broken: {marker}")
    for forbidden in [
        "element.click();",
        "actionButton.click();",
    ]:
        if forbidden in runner:
            raise SystemExit(f"battle mobile tap regressed to raw click: {forbidden}")


if "treasure-key-battle-handoff-20260928-r1" in s:
    gate=section("function battleExitState()","function battleLeaveBackButton")
    if "battle-reward-state-machine-20260928-r1" in s:
        for marker in [
            "rewardConfirmPending=battleRewardConfirmOnlyPending()",
            "|| rewardConfirmPending",
            "reason:'waiting-final-reward'",
            "if (battleFinalRewardClaimed)",
        ]:
            if marker not in gate:
                raise SystemExit(f"battle final-reward gate broken: {marker}")
        if "enemies.length>0 && battleFinalRewardClaimed" in gate:
            raise SystemExit("battle reward state regressed: stale enemy DOM resets claimed state")
    else:
        for marker in [
            "rewardConfirmPending=enemies.length===0 && !!battleRewardDismissButton()",
            "|| rewardConfirmPending",
            "reason:'waiting-final-reward'",
        ]:
            if marker not in gate:
                raise SystemExit(f"battle final-reward gate broken: {marker}")

    dismiss=section("async function dismissBattleRewardIfPresent","function dispatchBattleTap")
    for marker in [
        "dispatchBattleTap(button,'battle-dismiss-reward-'",
        "for (let i=0;i<3;i++)",
    ]:
        if marker not in dismiss:
            raise SystemExit(f"battle reward confirmation broken: {marker}")
    if "button.click();" in dismiss:
        raise SystemExit("battle reward confirmation regressed to raw click")

    intro=section("async function runBattleIntroAcknowledge","async function autoMapSkipBattleWithoutFight")
    if "battle-intro-overlay-ack-20260930-r1" in s:
        for marker in [
            "dispatchMinigameOverlaySafeTapAt(",
            "deviceNeutralActivate(",
            "waitDeviceNeutralCondition(accepted",
            "battle-intro-ack-retry",
        ]:
            if marker not in intro:
                raise SystemExit(f"battle intro overlay acknowledgement broken: {marker}")
    else:
        for marker in [
            "dispatchBattleTap(button,'battle-intro-ack')",
            "setTimeout(checkPuzzle,80)",
        ]:
            if marker not in intro:
                raise SystemExit(f"battle intro acknowledgement broken: {marker}")

    victory=section("async function runBattleVictoryClaim","async function runBattleAuto")
    if "battle-reward-state-machine-20260928-r1" in s:
        for marker in [
            "tapVictoryTile(victory,runId)",
            "battleRewardConfirmOnlyPending()",
            "const dismissed=await dismissBattleRewardIfPresent(runId);",
            "battleFinalRewardClaimed=true;",
            "battle-victory-confirm-only-complete",
        ]:
            if marker not in victory:
                raise SystemExit(f"battle final chest state machine broken: {marker}")

        reward_section=section("function battleVictoryElement()","async function runBattleAuto")
        for marker in [
            "function battleVictoryTileAction",
            "async function tapVictoryTile",
            "function battleRewardConfirmOnlyPending",
            "victory-tile-action",
        ]:
            if marker not in reward_section:
                raise SystemExit(f"battle reward tile action contract broken: {marker}")

        signature=section("function getSignature()","function checkPuzzle()")
        victory_pos=signature.find("const victory=battleVictoryElement();")
        sword_pos=signature.find("const sword = battleSwordElement();")
        if victory_pos<0 or sword_pos<0 or victory_pos>=sword_pos:
            raise SystemExit("battle reward priority broken: victory must outrank sword/enemy DOM")
        for marker in [
            "BATTLE_REWARD_CONFIRM|final",
            "battleRewardConfirmOnlyPending()",
        ]:
            if marker not in signature:
                raise SystemExit(f"battle reward signature contract broken: {marker}")

        run_battle=section("function runBattle()","// ----- Full Treasure Map orchestrator -----")
        for marker in [
            "if (battleFinalRewardClaimed)",
            "battle-stale-dom-after-reward",
        ]:
            if marker not in run_battle:
                raise SystemExit(f"stale battle DOM guard broken: {marker}")
        if "battleFinalRewardClaimed=false;" in run_battle:
            raise SystemExit("stale battle DOM guard broken: runBattle resets claimed state")

        intro_root=section("function battleIntroModalRoot","async function runBattleIntroAcknowledge")
        for marker in [
            "Сражение|Battle",
            "battleIntroAcknowledgeButton(root=battleIntroModalRoot())",
        ]:
            if marker not in intro_root:
                raise SystemExit(f"battle intro modal contract broken: {marker}")
    else:
        for marker in [
            "const dismissed=await dismissBattleRewardIfPresent(runId);",
            "const confirmPending=!!battleRewardDismissButton();",
            "const success=!battleVictoryModalRoot() && !confirmPending;",
            "battleFinalRewardClaimed=true;",
        ]:
            if marker not in victory:
                raise SystemExit(f"battle final chest handoff broken: {marker}")

    tick=section("async function runAutoMapTick","function setAutoMapEnabled")
    for marker in [
        "battlePreflightSignature.startsWith('BATTLE_REWARD')",
        "runBattleVictoryClaim()",
        "runBattleIntroAcknowledge()",
    ]:
        if marker not in tick:
            raise SystemExit(f"AutoMap battle preflight broken: {marker}")

    if "battle-reward-state-machine-20260928-r1" in s:
        for marker in [
            "const introModal=battleIntroModalRoot();",
            "battleFinalRewardClaimed",
            "battle-claimed-exit-retry",
        ]:
            if marker not in tick:
                raise SystemExit(f"AutoMap battle state machine broken: {marker}")

        complete=section("function autoMapCurrentModuleComplete","async function autoMapHandleExitOrContinue")
        if "return battleFinalRewardClaimed;" not in complete:
            raise SystemExit("battle claimed state must mark the module complete")
        exit_logic=section("async function autoMapHandleExitOrContinue","async function autoMapStartJourney")
        if "signature.startsWith('BATTLE') && !battleFinalRewardClaimed" not in exit_logic:
            raise SystemExit("battle claimed state must be allowed to exit")

        check=section("function checkPuzzle()","function start()")
        for marker in [
            "battleIntroModalRoot()",
            "(autoMapEnabled() || battleAutoEnabled())",
            "runBattleIntroAcknowledge()",
        ]:
            if marker not in check:
                raise SystemExit(f"battle intro independent dispatch broken: {marker}")
    else:
        if "battlePreflightSignature.startsWith('BATTLE|')" not in tick or "battlePreflightSignature.startsWith('BATTLE_PREVIEW|')" not in tick:
            raise SystemExit("legacy battle intro signature gate missing")
        check=section("function checkPuzzle()","function start()")
        if "isBattle || isBattlePreview" not in check or "battleIntroAcknowledgeButton()" not in check:
            raise SystemExit("battle intro must be acknowledged before normal solver dispatch")


if "battle-overlay-safe-targeting-20260928-r1" in s:
    board=section("function getBattleBoard()","function battleNeighbours")
    if "enemy_type_(01|02|03|04)" not in board:
        raise SystemExit("battle guardian contract broken: type_04 parser missing")

    element=section("function battleElementForSlot","function battleSwordElement")
    if "enemy_type_(01|02|03|04)" not in element:
        raise SystemExit("battle guardian contract broken: type_04 slot lookup missing")

    cost=section("function battleCostForElement","function battleActionButton")
    if "enemy_type_(?:01|02|03|04)" not in cost:
        raise SystemExit("battle guardian contract broken: type_04 cost parser missing")

    tap=section("function battleUiOverlays","function treasureChestCost")
    for marker in [
        "function battleElementFromPointIgnoringOverlays",
        "element.style.pointerEvents='none'",
        "HK_BATTLE_OVERLAY_SAFE_TARGETING_REV",
    ]:
        if marker not in tap:
            raise SystemExit(f"battle overlay-safe tap contract broken: {marker}")

    if "minigame-tap-isolation-lights-recovery-20260928-r1" in s:
        for marker in [
            "function dispatchBattleOverlaySafeTap(",
            "function dispatchBattleOverlaySafeTapAt(",
            "battleElementFromPointIgnoringOverlays(x,y,element)",
            "battleElementFromPointIgnoringOverlays(px,py,null)",
        ]:
            if marker not in tap:
                raise SystemExit(f"battle isolated overlay-safe tap contract broken: {marker}")

        generic=section("function dispatchBattleTap(element","function battleUiOverlays")
        if "battleElementFromPointIgnoringOverlays" in generic:
            raise SystemExit("shared minigame tap regressed into battle-only overlay filtering")
        if "document.elementFromPoint(x,y) || element" not in generic:
            raise SystemExit("shared minigame element tap must keep neutral elementFromPoint behavior")
        if "document.elementFromPoint(px,py)" not in generic:
            raise SystemExit("shared minigame coordinate tap must keep neutral elementFromPoint behavior")

    badge=section("function addNumber","function getLightsBoard")
    if "zIndex:'2147483647'" not in badge:
        raise SystemExit("battle solver badge must render above HK fixed toggles")
    if "zIndex:'9999999'" in badge:
        raise SystemExit("battle solver badge regressed below HK fixed toggles")

    run_battle=section("function runBattle()","// ----- Full Treasure Map orchestrator -----")
    for marker in [
        "battle-guardian-plan-coverage",
        "enemy.type==='04'",
        "selected:selectedSlots.has(enemy.slot)",
    ]:
        if marker not in run_battle:
            raise SystemExit(f"battle guardian plan diagnostic missing: {marker}")


if "battle-activated-final-reward-exit-20260928-r1" in s:
    reward=section("function battleFinalRewardElements","function battleVictoryModalRoot")
    for marker in [
        "function battleFinalRewardActivatedElement",
        "function battleFinalRewardSettled",
        "function battleRecoverFinalRewardClaimed",
        "Активировано|Activated",
        ".filter(element=>!battleFinalRewardActivatedText(element))",
        "battle-final-reward-recovered",
    ]:
        if marker not in reward:
            raise SystemExit(f"battle activated reward recovery broken: {marker}")

    if "!battleVictoryModalRoot()" not in reward or "!battleRewardDismissButton()" not in reward:
        raise SystemExit("activated reward must not count as settled while reward confirmation is open")

    signature=section("function getSignature()","function checkPuzzle()")
    for marker in [
        "battleRecoverFinalRewardClaimed('signature')",
        "BATTLE_COMPLETE|mf_fairlot_minigame_fight_room_big_chest",
    ]:
        if marker not in signature:
            raise SystemExit(f"battle activated completion signature broken: {marker}")
    complete_pos=signature.find("battleRecoverFinalRewardClaimed('signature')")
    victory_pos=signature.find("const victory=battleVictoryElement();")
    sword_pos=signature.find("const sword = battleSwordElement();")
    if complete_pos<0 or victory_pos<0 or sword_pos<0 or not (complete_pos < victory_pos < sword_pos):
        raise SystemExit("activated final reward must outrank pending reward and stale battle DOM")

    gate=section("function battleExitState()","function battleLeaveBackButton")
    for marker in [
        "activatedSettled=battleRecoverFinalRewardClaimed('exit-state')",
        "reason:'final-reward-activated'",
        "allowed:true",
    ]:
        if marker not in gate:
            raise SystemExit(f"battle activated exit gate broken: {marker}")

    tick=section("async function runAutoMapTick","function setAutoMapEnabled")
    required=[
        "battleRecoverFinalRewardClaimed('automap-preflight')",
        "battleAutoRunId+=1",
        "battleAutoRunning=false",
        "battle-activated-stale-runner-release",
        "battle-activated-exit-retry",
    ]
    if "battle-complete-exit-loop-20260930-r1" in s:
        required += ["autoMapRecoverCompletedBattleExit('automap-activated-reward')"]
        helper=section("async function autoMapRecoverCompletedBattleExit","function autoMapModalPrimaryButton")
        for marker in [
            "dispatchMinigameOverlaySafeTapAt(",
            "treasureGuideScreenVisible()",
            "battle-complete-exit-retry",
        ]:
            if marker not in helper:
                raise SystemExit(f"battle completed-exit loop broken: {marker}")
    else:
        required += ["autoMapHandleExitOrContinue()"]
    for marker in required:
        if marker not in tick:
            raise SystemExit(f"battle activated AutoMap exit handoff broken: {marker}")

print("TREASURE_BATTLE_FULL_CLEAR_CONTRACT=PASS")
