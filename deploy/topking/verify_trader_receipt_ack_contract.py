from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
  "trader-receipt-ack-20260928-r1",
  "function traderReceiptAcknowledgeButton(root)",
  "function traderReceiptModalRoot()",
  "async function traderAcknowledgeReceipt(source='trader-purchase')",
  "traderAcknowledgeReceipt('resume')",
  "traderAcknowledgeReceipt('post-purchase')",
  "deviceNeutralActivate(",
  "dispatchAutoMapTap(clickTarget,'trader-receipt-ack-fallback-'",
  "dispatchBattleTapAt(",
  "waitDeviceNeutralCondition(accepted,1600,70)",
  "traderReceiptAckRevision:HK_TRADER_RECEIPT_ACK_REV",
]
for marker in required:
    if marker not in s:
        raise SystemExit("trader receipt ack contract broken: "+marker)

# Keep the approved-purchase and exit handoff fixes that this patch depends on.
for marker in [
  "trader-approved-modal-buy-20260927-r1",
  "trader-exit-handoff-20260927-r1",
  "treasure-key-ack-after-purchase-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("required preserved marker missing: "+marker)

print("TRADER_RECEIPT_ACK_CONTRACT=PASS")
