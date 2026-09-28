from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

for marker in [
    "treasure-recorder-ui-removed-20260928-r1",
    "function treasureRunRecorderUpdateButton()",
    "document.getElementById('hkTreasureRunRecorderToggle')?.remove()",
    "treasureRecorderUiRemovedRevision:HK_TREASURE_RECORDER_UI_REMOVED_REV",
]:
    if marker not in s:
        raise SystemExit("recorder UI removal contract broken: "+marker)

for forbidden in [
    "treasureRunRecorderButton=document.createElement('button')",
    "'Запись карты: ВЫКЛ'",
    "'Запись карты: ВКЛ #'",
]:
    if forbidden in s:
        raise SystemExit("retired recorder UI still present: "+forbidden)

# Recorder internals and all current gameplay fixes stay intact.
for marker in [
    "treasure-run-recorder-20260926-r1",
    "treasure-run-recorder-stability-blockers-20260926-r2",
    "purchase-confirm-fast-global-20260928-r1",
    "trader-receipt-ack-20260928-r1",
    "treasure-dig-fast-pacing-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("preserved marker missing: "+marker)

print("TREASURE_RECORDER_UI_REMOVED_CONTRACT=PASS")
