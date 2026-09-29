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

required=[
    "chest-phase-order-20260929-r1",
    "chest-uncommitted-retry-20260929-r1",
    "function treasureChestDigVisualPending",
    "function treasureChestWorkState",
    "function treasureChestUncommittedRollback",
]
for marker in required:
    if marker not in s:
        raise SystemExit(f"missing marker: {marker}")

work=section("    function treasureChestWorkState() {","    function treasureChestTarget() {")
positions=[
    work.find("if (diggingRows.length)"),
    work.find("if (chestRows.length)"),
    work.find("if (keyOffers.length)")
]
if min(positions)<0 or positions != sorted(positions):
    raise SystemExit(f"phase order broken: {positions}")
if "treasureChestUnboughtCount" in work:
    raise SystemExit("backend is_bought still vetoes visible digging rows")
if "phase:'dig'" not in work or "phase:'chest'" not in work or "phase:'post'" not in work:
    raise SystemExit("missing strict phase markers")

target=section("    function treasureChestTarget() {","    function treasureCenteredModalRoot() {")
if "treasureChestWorkState()" not in target:
    raise SystemExit("target does not use phase work state")
if "remainingDigging:state.diggingRows.length" not in target:
    raise SystemExit("chest selection is not proving zero digging first")

runner=section("    async function runTreasureChestAuto() {","    function battleFinalRewardElements() {")
for marker in [
    "beforeBalance,",
    "cost:target.cost ? {...target.cost} : null",
    "phase:String(target.phase||'')",
    "chestPendingLotGate={",
]:
    if marker not in runner:
        raise SystemExit(f"pending gate receipt missing: {marker}")

gate=section("    function treasureChestUncommittedRollback","    async function runTreasureChestAuto() {")
for marker in [
    "age<9000",
    "treasureChestLotState(gate.lotId)",
    "walletAmount(itemId)",
    "now!==before",
    "action-not-committed",
    "chest-lot-uncommitted-rollback",
]:
    if marker not in gate:
        raise SystemExit(f"uncommitted rollback contract missing: {marker}")

auto=section("        if (signature.startsWith('CHESTS|')) {","        // Between rooms")
for marker in [
    "const work=treasureChestWorkState();",
    "work.phase==='dig'",
    "work.pending>0",
    "chest-phase-wait",
    "await autoMapHandleExitOrContinue()",
]:
    if marker not in auto:
        raise SystemExit(f"automap chest phase contract missing: {marker}")
if auto.find("work.pending>0") > auto.find("await autoMapHandleExitOrContinue()"):
    raise SystemExit("exit may occur before pending-work gate")

print("TREASURE_CHEST_PHASE_ORDER_CONTRACT=PASS")
