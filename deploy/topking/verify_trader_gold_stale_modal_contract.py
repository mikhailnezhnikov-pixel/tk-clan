from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
  "// @version      1.18.83",
  "trader-gold-stale-modal-reset-20260929-r1",
  "function traderForbiddenGoldRow(row)",
  "JSON.stringify(catalog?.reward||{})",
  "if (traderForbiddenGoldRow(row))",
  "function traderForbiddenGoldCloseButton",
  "async function traderDismissForbiddenGoldModal",
  "trader-forbidden-gold-close-corner-",
  "auto-map-forbidden-gold-confirm-blocked",
  "await traderDismissForbiddenGoldModal('auto-map-confirm-guard')",
  "const forbiddenGoldModal=traderForbiddenGoldModalRoot();",
  "autoMapStatus('закрываю Золотые монеты'",
  "forbidden-gold-modal-retry",
  "forbidden-gold-overlay",
  "traderGoldStaleModalRevision:HK_TRADER_GOLD_STALE_MODAL_REV",
]
for marker in required:
    if marker not in s:
        raise SystemExit("trader gold stale-modal contract broken: "+marker)

# The deny rule must run before the permissive ID whitelist.
row_start=s.find("function traderApprovedRow(row)")
row_end=s.find("function traderValueTier",row_start)
row=s[row_start:row_end]
if row.find("traderForbiddenGoldRow(row)")<0 or row.find("traderApprovedLot(row.lotId)")<0:
    raise SystemExit("traderApprovedRow guards missing")
if row.find("traderForbiddenGoldRow(row)")>row.find("traderApprovedLot(row.lotId)"):
    raise SystemExit("gold deny-list runs after permissive whitelist")

# The global AutoMap preflight must handle gold before leave-confirm recovery.
tick_start=s.find("async function runAutoMapTick")
tick_end=s.find("function setAutoMapEnabled",tick_start)
tick=s[tick_start:tick_end]
gold=tick.find("const forbiddenGoldModal=traderForbiddenGoldModalRoot();")
leave=tick.find("if (autoMapLeaveModalRoot())")
if gold<0 or leave<0 or gold>leave:
    raise SystemExit("gold stale modal does not outrank leave/map logic")

# Keep prior battle/map/trader fixes.
for marker in [
  "trader-gold-currency-skip-20260928-r1",
  "trader-receipt-ack-20260928-r1",
  "purchase-confirm-fast-global-20260928-r1",
  "battle-visible-point-truth-20260929-r1",
  "battle-full-fair-state-20260928-r1",
  "chest-visible-claim-priority-20260928-r1",
  "clan-crest-launcher-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("preserved marker missing: "+marker)

print("TRADER_GOLD_STALE_MODAL_CONTRACT=PASS")
