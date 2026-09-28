from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

global_fast_confirm="purchase-confirm-fast-global-20260928-r1" in s
required=[
  "treasure-dig-fast-pacing-20260928-r1",
  "async function chestDigPause",
  "scan:[90,160]",
  "aim:[70,130]",
  ("confirm:[100,180]" if global_fast_confirm else "confirm:[110,190]"),
  "settle:[180,300]",
  "target?.digging ? chestDigPause('scan'",
  "target.digging ? chestDigPause('aim'",
  "target.digging ? chestDigPause('confirm'",
  "target.digging ? chestDigPause('settle'",
  "target?.digging ? minigameRandomMs(180,320)",
  "treasureDigFastRevision:HK_TREASURE_DIG_FAST_REV",
]
for marker in required:
    if marker not in s:
        raise SystemExit("dig fast pacing contract broken: "+marker)

# Existing chest safety and trader/key fixes must remain intact.
for marker in [
  "treasure-chest-fast-pacing-20260927-r1",
  "treasure-chest-map-foreground-guard-20260927-r1",
  "waitTreasureModal(target.cost,runId)",
  "waitTreasureActionButton(modal,target.cost,runId)",
  "CHEST_ACTION_TIMEOUT_MS",
  "trader-receipt-ack-20260928-r1",
  "treasure-key-ack-after-purchase-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("required preserved marker missing: "+marker)

# Ordinary chest scan/aim/settle stay unchanged. Confirm may use the global
# 100–180 ms purchase-confirm path introduced after 1.18.72.
for marker in [
  "scan:[600,950]",
  "aim:[380,650]",
  ("confirm:[100,180]" if global_fast_confirm else "confirm:[650,1050]"),
  "settle:[950,1500]",
]:
    if marker not in s:
        raise SystemExit("ordinary chest pacing changed: "+marker)

print("TREASURE_DIG_FAST_CONTRACT=PASS")
