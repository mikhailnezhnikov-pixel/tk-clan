from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
    "// @version      1.18.88",
    "treasure-transaction-gate-20260929-r1",
    "treasure-stale-modal-hard-gate-20260929-r1",
    "chest-lot-hard-gate-20260929-r1",
    "treasure-key-global-gate-20260929-r1",
    "battle-offscreen-action-scroll-20260929-r1",
    "function battleScrollHost(element=null)",
    "battleScrollTargetIntoViewportAsync(\n          actionButton",
    "battle-action-slot-",
    "let chestPendingLotGate = null;",
    "function treasureChestLotState(lotId)",
    "function treasureChestReconcilePendingGate()",
    "lot-state-unconfirmed",
    "function autoMapTxnCanSelectNextCell()",
    "autoMapTxnSet('TARGET_FOUND'",
    "autoMapTxnSet('CARD_OPENED'",
    "autoMapTxnSet('ACTION_CONFIRMED'",
    "autoMapTxnSet('SERVER_UI_STATE_CHANGED'",
    "autoMapTxnSet('ROOM_COMPLETE'",
    "autoMapTxnSet('EXIT_CONFIRMED'",
    "autoMapTxnMarkMapVisible('tick-preflight')",
    "autoMapCancelStaleRunners('treasure-key-global-gate')",
]
for marker in required:
    if marker not in s:
        raise SystemExit("treasure transaction gate contract broken: "+marker)

# 1) stale modal must verify actual disappearance, not just sleep and continue.
start=s.find("async function autoMapCloseLingeringModal")
end=s.find("function autoMapJourneyButton",start)
block=s[start:end]
for marker in [
    "while (Date.now()-started<2600)",
    "if (!current || current!==root)",
    "treasure-stale-modal-hard-gate-clear",
    "treasure-stale-modal-hard-gate-block",
]:
    if marker not in block:
        raise SystemExit("stale modal hard gate missing: "+marker)

# 2) battle action must scroll exact action button before tap.
start=s.find("async function runBattleAuto(solution)")
end=s.find("async function runBattleInsufficientExit",start)
battle=s[start:end]
scroll=battle.find("battleScrollTargetIntoViewportAsync(\n          actionButton")
tap=battle.find("dispatchBattleOverlaySafeTap(actionButton,'battle-confirm-attack')")
if scroll<0 or tap<0 or scroll>tap:
    raise SystemExit("battle action scroll must precede attack confirmation")

# 3) chest cannot unlock on mere modal disappearance.
start=s.find("async function runTreasureChestAuto()")
end=s.find("function battleFinalRewardElements",start)
chest=s[start:end]
if "changed || reward || !treasureModalRoot(target.cost)" in chest:
    raise SystemExit("legacy chest modal-disappearance success gate still present")
for marker in [
    "beforeLotState=treasureChestLotState(target.lotId)",
    "chestPendingLotGate={",
    "if (lotState!==beforeLotState)",
    "if (!hardConfirmed)",
    "treasureChestClearPendingGate",
]:
    if marker not in chest:
        raise SystemExit("chest exact-lot hard gate missing: "+marker)

# 4) treasure key preflight is global, not limited to idle child modules.
start=s.find("async function runAutoMapTick(source='loop')")
end=s.find("function setAutoMapEnabled",start)
tick=s[start:end]
if "keyModal && !autoMapModulesRunning()" in tick:
    raise SystemExit("treasure key remains incorrectly limited to idle modules")
for marker in [
    "const interrupted=autoMapCancelStaleRunners('treasure-key-global-gate')",
    "return await autoMapBuyTreasureKeyIfPresent()" if False else "const done=await autoMapBuyTreasureKeyIfPresent()",
]:
    if marker not in tick:
        raise SystemExit("global treasure key gate missing: "+marker)

# 5) new cell selection is physically gated by MAP_VISIBLE/transaction state.
if s.count("if (!autoMapTxnCanSelectNextCell())") < 2:
    raise SystemExit("next-cell transaction gate missing on one map traversal path")

# Preserve critical existing behavior.
for marker in [
    "battle-preview-resume-20260929-r1",
    "battle-intro-hard-gate-20260929-r1",
    "battle-visible-point-truth-20260929-r1",
    "battle-full-fair-state-20260928-r1",
    "battle-egg-one-berry-buy-20260928-r1",
    "lights-confirm-ack-before-board-reward-gate-20260928-r1",
    "lights-hint-canon-fixed-plan-map6-20260928-r1",
    "trader-gold-exact-purchase-modal-20260929-r1",
    "trader-gold-currency-skip-20260928-r1",
    "treasure-automap-module-ownership-20260927-r1",
]:
    if marker not in s:
        raise SystemExit("preserved behavior missing: "+marker)

print("TREASURE_TRANSACTION_GATES_CONTRACT=PASS")
