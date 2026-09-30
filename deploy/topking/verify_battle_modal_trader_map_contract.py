from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
    "// @version      1.18.96",
    "const BUILD_VERSION = '1.18.96';",
    "battle-open-modal-priority-20260930-r1",
    "trader-map-modal-approval-20260930-r1",
    "battle-intro-overlay-ack-20260930-r1",
    "battle-complete-exit-loop-20260930-r1",
    "battle-open-modal-confirm-20260930-r1",
]
for marker in required:
    if marker not in s:
        raise SystemExit("1.18.96 contract missing: "+marker)

trader_start=s.find("function traderModalApproved(root)")
trader_end=s.find("function traderClickableTarget",trader_start)
if trader_start<0 or trader_end<0:
    raise SystemExit("trader modal approval block missing")
trader=s[trader_start:trader_end]
for marker in [
    r"/карта\s+сокровищ|treasure\s+map/i.test(text)",
    r"/золотые\s+монеты|gold(?:en)?\s+coins|cur_gold/i.test(text)",
]:
    if marker not in trader:
        raise SystemExit("trader map modal contract missing: "+marker)

action_start=s.find("function battleEnemyModalActionButton(expectedCost=null)")
action_end=s.find("function battleEnemyModalRoot()",action_start)
if action_start<0 or action_end<0:
    raise SystemExit("battle modal action inference block missing")
action=s[action_start:action_end]
for marker in [
    "const hasExpected=",
    "battleEnemyModalActionCost(element)",
    "if (!hasExpected)",
    "rect.top<rr.top+rr.height*0.66",
    "rect.width<rr.width*0.34",
    "HK_BATTLE_OPEN_MODAL_PRIORITY_REV",
]:
    if marker not in action:
        raise SystemExit("battle modal action inference contract missing: "+marker)

confirm_start=s.find("async function battleConfirmAlreadyOpenEnemyModal")
confirm_end=s.find("function battleActionButton",confirm_start)
if confirm_start<0 or confirm_end<0:
    raise SystemExit("battle open modal confirmation block missing")
confirm=s[confirm_start:confirm_end]
for marker in [
    "const resolvedCost=",
    "async function runBattleOpenEnemyModalRecovery",
    "battleEnemyModalActionButton(null)",
    "battle-open-modal-priority-start",
    "battleInsufficientExitNotBefore=Date.now()+900",
]:
    if marker not in confirm:
        raise SystemExit("battle open modal priority contract missing: "+marker)

exit_start=s.find("function battleExitState()")
exit_end=s.find("function battleLeaveBackButton",exit_start)
if exit_start<0 or exit_end<0:
    raise SystemExit("battle exit state block missing")
exit_block=s[exit_start:exit_end]
for marker in [
    "const enemyModalPending=!!battleEnemyModalRoot();",
    "reason:'enemy-modal-pending'",
]:
    if marker not in exit_block:
        raise SystemExit("battle exit modal gate missing: "+marker)

run_start=s.find("function runBattle()")
run_end=s.find("// ----- Full Treasure Map orchestrator",run_start)
if run_start<0 or run_end<0:
    raise SystemExit("runBattle block missing")
run=s[run_start:run_end]
modal_gate=run.find("if (battleEnemyModalRoot())")
egg_gate=run.find("const eggOffer=battleEggOfferTarget()")
insufficient=run.find("runBattleInsufficientExit")
if modal_gate<0 or egg_gate<0 or insufficient<0:
    raise SystemExit("runBattle priority markers missing")
if not (modal_gate < egg_gate < insufficient):
    raise SystemExit("open enemy modal is not prioritized before battle exit decisions")
for marker in [
    "runBattleOpenEnemyModalRecovery('run-battle-hard-gate')",
    "сражение → подтверждаю бой",
]:
    if marker not in run:
        raise SystemExit("runBattle hard gate contract missing: "+marker)

exports=s[s.find("window.hkCore"):s.find("window.hkCore")+50000]
for marker in [
    "traderMapModalRevision:HK_TRADER_MAP_MODAL_REV",
    "battleOpenModalPriorityRevision:HK_BATTLE_OPEN_MODAL_PRIORITY_REV",
]:
    if marker not in exports:
        raise SystemExit("debug revision export missing: "+marker)

print("BATTLE_MODAL_TRADER_MAP_CONTRACT=PASS")
