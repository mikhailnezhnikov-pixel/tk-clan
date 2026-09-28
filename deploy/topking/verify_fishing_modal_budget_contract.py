from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
  "fishing-modal-budget-ownership-20260928-r1",
  "function fishingPurchaseModalOpen()",
  "function fishingAffordableInsideOpenModal(cost)",
  "if (casts===null && fishingPurchaseModalOpen()) return true;",
  "fishing-auto-exit-blocked-modal",
  "phase:'budget-empty'",
  "phase:'post-scan'",
  "if (!fishingAffordableInsideOpenModal(target.cost))",
  "fishingModalBudgetRevision:HK_FISHING_MODAL_BUDGET_REV",
]
for marker in required:
    if marker not in s:
        raise SystemExit("fishing modal budget contract broken: "+marker)

for forbidden in [
  "if (!fishingAffordable(target.cost)) return null;",
]:
    if forbidden in s:
        raise SystemExit("premature fishing modal exit condition still present: "+forbidden)

# Preserve current purchase speed and exit safety.
for marker in [
  "purchase-confirm-fast-global-20260928-r1",
  "fishing-zero-cast-exit-20260927-r1",
  "fishing-human-fast-20260927-r1",
  "treasure-auto-map-foreground-handoff-20260926-r6",
  "treasure-auto-map-stale-runner-20260927-r2",
]:
    if marker not in s:
        raise SystemExit("preserved marker missing: "+marker)

print("FISHING_MODAL_BUDGET_CONTRACT=PASS")
