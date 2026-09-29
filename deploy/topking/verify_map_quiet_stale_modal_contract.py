from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
  "// @version      1.18.89",
  "treasure-map-quiet-gate-20260929-r1",
  "stale-modal-shell-close-20260929-r1",
  "const AUTO_MAP_QUIET_MS=1400",
  "let autoMapMapQuietSince=0",
  "function autoMapModalShell(root)",
  "deviceNeutralActivate(",
  "stale-modal-shell-corner-",
  "function autoMapTxnMarkMapVisible",
  "setTimeout(()=>void runAutoMapTick('map-quiet-gate'),180)",
]
for marker in required:
    if marker not in s:
        raise SystemExit("map quiet/stale modal contract broken: "+marker)

start=s.find("function autoMapTxnMarkMapVisible")
end=s.find("function autoMapEnabled",start)
block=s[start:end]
for marker in [
    "if (treasureModalRoot(null))",
    "if (!autoMapMapQuietSince)",
    "if (quietFor<AUTO_MAP_QUIET_MS)",
    "autoMapTxnSet('MAP_VISIBLE'",
]:
    if marker not in block:
        raise SystemExit("map quiet gate missing: "+marker)

start=s.find("async function autoMapCloseLingeringModal")
end=s.find("function autoMapJourneyButton",start)
block=s[start:end]
for marker in [
    "const shellInfo=autoMapModalShell(inner)",
    "deviceNeutralActivate(",
    "waitDeviceNeutralCondition(accepted",
    "autoMapMapQuietSince=0",
]:
    if marker not in block:
        raise SystemExit("stale shell close missing: "+marker)

start=s.find("async function runAutoMapTick(source='loop')")
end=s.find("function setAutoMapEnabled",start)
block=s[start:end]
if "const mapReady=autoMapTxnMarkMapVisible('tick-preflight')" not in block:
    raise SystemExit("map quiet preflight missing")
if "if (!mapReady)" not in block:
    raise SystemExit("map quiet preflight does not stop next-cell selection")

for marker in [
  "treasure-transaction-gate-20260929-r1",
  "chest-lot-hard-gate-20260929-r1",
  "treasure-key-global-gate-20260929-r1",
  "battle-offscreen-action-scroll-20260929-r1",
  "lights-confirm-ack-before-board-reward-gate-20260928-r1",
  "trader-gold-exact-purchase-modal-20260929-r1",
]:
    if marker not in s:
        raise SystemExit("preserved behavior missing: "+marker)

print("MAP_QUIET_STALE_MODAL_CONTRACT=PASS")
