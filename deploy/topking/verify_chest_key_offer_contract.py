from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
  "chest-key-offer-buy-20260928-r1",
  "function treasureChestKeyOfferElements()",
  "item_treasurehunt_key_(?:common|uncommon|rare|epic|legendary)",
  "cost={id:'item_treasurehunt_energy',quantity};",
  "treasureChestKeyOfferElements().forEach",
  "priority:1400",
  "KEY_OFFERS=",
  "target.keyOffer?'chest-buy-key-card'",
  "target.keyOffer?'chest-buy-key-confirm'",
  "chestKeyOfferRevision:HK_CHEST_KEY_OFFER_REV",
]
for marker in required:
    if marker not in s:
        raise SystemExit("chest key offer contract broken: "+marker)

for marker in [
  "treasure-chest-fast-pacing-20260927-r1",
  "treasure-dig-fast-pacing-20260928-r1",
  "purchase-confirm-fast-global-20260928-r1",
  "treasure-key-any-rarity-20260928-r1",
  "treasure-key-ack-after-purchase-20260928-r1",
  "trader-gold-currency-skip-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("preserved marker missing: "+marker)

print("CHEST_KEY_OFFER_CONTRACT=PASS")
