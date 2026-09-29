from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
  "automation-toggle-trusted-input-20260929-r1",
  "coordinate-overlay-guard-20260929-r1",
  "automation-toggle-synthetic-blocked",
  "dispatchMinigameOverlaySafeTapAt(x,rr.top+rr.height*fraction,'chest-action-fallback-'",
  "dispatchMinigameOverlaySafeTapAt(x,rr.top+rr.height*fraction,'victory-fallback-'",
]
for marker in required:
    if marker not in s:
        raise SystemExit("automation toggle guard contract broken: "+marker)

# Every floating automation toggle must reject synthetic clicks.
for toggle in [
  "battleAutoToggle",
  "chestAutoToggle",
  "lightsAutoToggle",
  "fishingAutoToggle",
  "traderAutoToggle",
  "autoMapToggle",
]:
    idx=s.find(toggle+".addEventListener('click',event=>{")
    if idx<0:
        raise SystemExit("toggle handler missing: "+toggle)
    block=s[idx:idx+800]
    if "if (!event.isTrusted)" not in block:
        raise SystemExit("toggle lacks trusted-input guard: "+toggle)

# Automated coordinate fallbacks in live modules must not use raw overlay-blind
# resolver. The function definition itself is intentionally preserved.
for label in [
  "trader-forbidden-gold-close-corner-",
  "trader-receipt-ack-center-",
  "trader-approved-modal-confirm-center",
  "trader-confirm-center-",
  "chest-action-fallback-",
  "victory-fallback-",
]:
    pos=s.find(label)
    if pos<0:
        raise SystemExit("fallback label missing: "+label)
    before=s[max(0,pos-220):pos]
    if "dispatchMinigameOverlaySafeTapAt(" not in before:
        raise SystemExit("fallback is not overlay-safe: "+label)

for marker in [
  "treasure-map-quiet-gate-20260929-r1",
  "stale-modal-shell-close-20260929-r1",
  "treasure-transaction-gate-20260929-r1",
  "chest-lot-hard-gate-20260929-r1",
  "treasure-key-global-gate-20260929-r1",
  "battle-offscreen-action-scroll-20260929-r1",
  "lights-confirm-ack-before-board-reward-gate-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("preserved behavior missing: "+marker)

print("AUTOMATION_TOGGLE_GUARD_CONTRACT=PASS")
