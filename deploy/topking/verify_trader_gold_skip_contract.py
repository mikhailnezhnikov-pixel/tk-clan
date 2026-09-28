from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
  "trader-gold-currency-skip-20260928-r1",
  "function traderForbiddenGoldLot(lotId)",
  "verse_gold4(?:coins|food)",
  "if (traderForbiddenGoldLot(id)) return false;",
  "traderForbiddenGoldLot(row.lotId)",
  "золотые\\s+монеты",
  "function traderForbiddenGoldModalRoot()",
  "function traderCloseForbiddenGoldModal",
  "trader-forbidden-gold-close",
  "trader-forbidden-gold-skip",
  "if (traderForbiddenGoldModalRoot()) return false;",
  "traderGoldSkipRevision:HK_TRADER_GOLD_SKIP_REV",
]
for marker in required:
    if marker not in s:
        raise SystemExit("trader gold skip contract broken: "+marker)

# The approved purchase families and current safety fixes must remain.
for marker in [
  "random4coins",
  "item_treasurehunt_key_",
  "карта\\s+сокровищ",
  "trader-receipt-ack-20260928-r1",
  "purchase-confirm-fast-global-20260928-r1",
  "fishing-modal-budget-ownership-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("preserved trader/current marker missing: "+marker)

print("TRADER_GOLD_SKIP_CONTRACT=PASS")
