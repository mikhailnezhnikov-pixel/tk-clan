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

if "treasure-key-ack-after-purchase-20260928-r1" in s:
    helpers=section("function autoMapTreasureKeyAcknowledgeButton","function autoMapTreasureKeyPurchaseButton")
    for marker in [
        "Понятно|Got it|Understood|OK|Okay",
        "autoMapAcknowledgeTreasureKey",
        "deviceNeutralActivate",
        "treasure-key-acknowledged",
        "runAutoMapTick('treasure-key-acknowledged')",
    ]:
        if marker not in helpers:
            raise SystemExit(f"key acknowledgement contract broken: {marker}")

    buy=section("async function autoMapBuyTreasureKeyIfPresent","async function autoMapWaitModal")
    for marker in [
        "initialAck",
        "initialTarget",
        "already-received",
        "after-purchase",
        "treasure-key-receipt-visible",
        "autoMapTreasureKeyAcknowledgeButton(root)",
    ]:
        if marker not in buy:
            raise SystemExit(f"key post-purchase contract broken: {marker}")

    # A receipt modal with only "Понятно" must not fall through to the old
    # "жду кнопку" stall path.
    ack_pos=buy.find("if (initialAck)")
    if ack_pos<0:
        ack_pos=buy.find("if (initialAck && !initialTarget?.element)")
    wait_pos=buy.find("ключ · жду кнопку")
    if ack_pos<0 or wait_pos<0 or ack_pos>=wait_pos:
        raise SystemExit("key acknowledgement must outrank missing purchase-button stall")

print("TREASURE_KEY_ACK_CONTRACT=PASS")
