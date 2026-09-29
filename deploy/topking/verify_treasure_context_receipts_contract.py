from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
  "battle-context-foreground-20260929-r1",
  "treasure-key-receipt-priority-20260929-r1",
  "treasury-corridor-ack-20260929-r1",
  "treasure-map-dominates-stale-minigame-20260929-r1",
  "function battleScreenVisiblyCurrent()",
  "function autoMapTreasuryCorridorModalRoot()",
  "function autoMapAcknowledgeTreasuryCorridor()",
]
for marker in required:
    if marker not in s:
        raise SystemExit("treasure context/receipt contract broken: "+marker)

# Battle intro generic "Понятно" must require visible battle screen.
start=s.find("function battleIntroModalRoot()")
end=s.find("function battleIntroTransitionLocked",start)
block=s[start:end]
if "if (!battleScreenVisiblyCurrent()) return null;" not in block:
    raise SystemExit("battle intro lacks visible-screen hard gate")

# Treasure-key acknowledgement must outrank purchase heuristic.
start=s.find("async function autoMapBuyTreasureKeyIfPresent()")
end=s.find("async function autoMapWaitModal",start)
block=s[start:end]
if "if (initialAck)" not in block:
    raise SystemExit("initial key receipt does not outrank purchase")
if "if (ack)" not in block:
    raise SystemExit("post-purchase key receipt does not outrank purchase")

# Treasury corridor acknowledgement must run before battle preview/intro.
start=s.find("async function runAutoMapTick(source='loop')")
end=s.find("function setAutoMapEnabled",start)
block=s[start:end]
treasury=block.find("const treasuryCorridorModal=autoMapTreasuryCorridorModalRoot();")
battle=block.find("const openBattlePreview=autoMapBattlePreviewRoot();")
if treasury<0 or battle<0 or treasury>battle:
    raise SystemExit("treasury corridor ack does not outrank battle preflight")

# Completed/active map must dominate stale minigame DOM in signature.
start=s.find("function getSignature()")
end=s.find("function checkPuzzle()",start)
block=s[start:end]
if "if (realMapForeground || completedMapForeground)" not in block:
    raise SystemExit("map dominance gate missing from signature")

for marker in [
  "automation-toggle-trusted-input-20260929-r1",
  "coordinate-overlay-guard-20260929-r1",
  "treasure-map-quiet-gate-20260929-r1",
  "chest-lot-hard-gate-20260929-r1",
  "battle-offscreen-action-scroll-20260929-r1",
  "lights-confirm-ack-before-board-reward-gate-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("preserved behavior missing: "+marker)

print("TREASURE_CONTEXT_RECEIPTS_CONTRACT=PASS")
