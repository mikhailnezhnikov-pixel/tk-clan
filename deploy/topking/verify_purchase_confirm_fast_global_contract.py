from pathlib import Path
import sys,re

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

if "purchase-confirm-fast-global-20260928-r1" not in s:
    raise SystemExit("global purchase-confirm marker missing")

def section(start,end):
    a=s.find(start)
    if a<0:
        raise SystemExit("missing section: "+start)
    b=s.find(end,a+len(start))
    if b<0:
        raise SystemExit("missing section end: "+end)
    return s[a:b]

sections=[
    ("async function minigameHumanPause","async function chestDigPause","generic"),
    ("async function chestDigPause","async function chestHumanPause","dig"),
    ("async function chestHumanPause","async function traderHumanPause","chest"),
    ("async function traderHumanPause","async function fishingHumanPause","trader"),
    ("async function fishingHumanPause","function minigameRecentHttpError","fishing"),
]

for start,end,label in sections:
    part=section(start,end)
    if "confirm:[100,180]" not in part:
        raise SystemExit(f"{label} purchase confirm is not 100-180 ms")

# The fast confirm must not remove post-click result verification.
for marker in [
    "waitTreasureModal(target.cost,runId)",
    "waitTreasureActionButton(modal,target.cost,runId)",
    "CHEST_ACTION_TIMEOUT_MS",
    "traderTargetResolved(target)",
    "fishingTargetResolved(target)",
    "autoMapStateFingerprint()",
]:
    if marker not in s:
        raise SystemExit("result-verification marker missing: "+marker)

# Rate-limit / transient-error protection stays untouched.
for marker in [
    "status===429",
    "minigameRandomMs(14000,19000)",
    "status===409",
    "minigameRecentHttpError",
]:
    if marker not in s:
        raise SystemExit("backoff safety marker missing: "+marker)

# Existing fixes that must survive this timing-only release.
for marker in [
    "treasure-dig-fast-pacing-20260928-r1",
    "treasure-chest-fast-pacing-20260927-r1",
    "trader-receipt-ack-20260928-r1",
    "treasure-key-ack-after-purchase-20260928-r1",
    "shop-fast-pacing-restore-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("preserved fix missing: "+marker)

print("PURCHASE_CONFIRM_FAST_GLOBAL_CONTRACT=PASS")
