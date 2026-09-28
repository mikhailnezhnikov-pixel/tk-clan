from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
  "chest-visible-key-balance-20260928-r1",
  "function treasureChestCardUsable(element)",
  "function treasureChestVisibleKeyBalance(element,text='')",
  "treasureChestAffordable(cost,row.element,row.text)",
  "treasure-chest-visible-key-balance",
  "treasure-chest-visible-overrides-stale-state",
  "lotId==='mf_treasurelot_chest_type_02') priority=1320",
  "lotId==='mf_treasurelot_chest_type_03') priority=1330",
  "chestVisibleKeyBalanceRevision:HK_CHEST_VISIBLE_KEY_BALANCE_REV",
  "/ключ[ ]+сокровищ|treasure[ ]+key/i.test(text)",
]
for marker in required:
    if marker not in s:
        raise SystemExit("visible key chest contract broken: "+marker)

for marker in [
  "chest-key-offer-buy-20260928-r1",
  "treasure-chest-fast-pacing-20260927-r1",
  "treasure-dig-fast-pacing-20260928-r1",
  "purchase-confirm-fast-global-20260928-r1",
  "trader-gold-currency-skip-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("preserved marker missing: "+marker)

print("CHEST_VISIBLE_KEY_BALANCE_CONTRACT=PASS")
