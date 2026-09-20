from pathlib import Path
import base64, zlib, hashlib

path = Path("/tmp/HamsterKingMobile.user.js")
text = path.read_text(encoding="utf-8")

old_marker = "const HK_STAGE2J_BOSSES_REV = 'bosses-canon-core-20260920-r1';"
new_marker = "const HK_STAGE2J_BOSSES_REV = 'bosses-area-target-20260920-r2';"
if old_marker not in text:
    raise SystemExit("expected Bosses r1 marker not found")
text = text.replace(old_marker, new_marker, 1)

start_anchor = "  function bossStateRows(documentValue = bossSnapshot || hkStateStore.snapshot || playerDocument) {"
end_anchor = "      function renderWars() {"
start = text.find(start_anchor)
end = text.find(end_anchor, start)
if start < 0 or end < 0 or end <= start:
    raise SystemExit("Bosses core block anchors not found")

payload = Path("deploy/topking/boss_core_r2.zb64").read_text(encoding="utf-8").strip()
core_bytes = zlib.decompress(base64.b64decode(payload))
expected_core_sha = "1fb223aad59e0a87d12c6937a44a33dc814e25ce1af847d59c648f6c5c6f3ed4"
actual_core_sha = hashlib.sha256(core_bytes).hexdigest()
if actual_core_sha != expected_core_sha:
    raise SystemExit(f"Bosses r2 core SHA mismatch: {actual_core_sha}")
replacement = core_bytes.decode("utf-8")
text = text[:start] + replacement + "\n      " + text[end:]

required = [
    "HK_BOSSES_CANON_REV='bosses-canon-core-20260920-r1'",
    "HK_BOSSES_TARGET_REV='bosses-area-target-20260920-r2'",
    "function bossCanonTargetPlan",
    "function bossCanonRewardOnlyPlan",
    "async function bossCanonRunAreaTargetContinuation",
    "data-boss-target-level",
    "data-boss-target-strategy",
    "data-boss-daily-base-runs",
    "'/battlepass?battle_pass_type='",
    "'/player/boxes/open?item_id='",
]
for needle in required:
    if needle not in text:
        raise SystemExit(f"missing invariant after patch: {needle}")

path.write_text(text, encoding="utf-8")
print("Bosses Area target r2 patch applied")
