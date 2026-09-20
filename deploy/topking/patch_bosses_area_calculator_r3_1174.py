from pathlib import Path
import base64, zlib, hashlib

path = Path("/tmp/HamsterKingMobile.user.js")
text = path.read_text(encoding="utf-8")

old_marker = "const HK_STAGE2J_BOSSES_REV = 'bosses-area-target-20260920-r2';"
new_marker = "const HK_STAGE2J_BOSSES_REV = 'bosses-area-calculator-20260920-r3';"
if old_marker not in text:
    raise SystemExit("expected Bosses r2 marker not found")
text = text.replace(old_marker, new_marker, 1)

start_anchor = "  function bossStateRows(documentValue = bossSnapshot || hkStateStore.snapshot || playerDocument) {"
end_anchor = "      function renderWars() {"
start = text.find(start_anchor)
end = text.find(end_anchor, start)
if start < 0 or end < 0 or end <= start:
    raise SystemExit("Bosses core block anchors not found")

payload = (
    Path("deploy/topking/boss_core_r3.part0").read_text(encoding="utf-8").strip()
    + Path("deploy/topking/boss_core_r3.part1").read_text(encoding="utf-8").strip()
)
core_bytes = zlib.decompress(base64.b64decode(payload))
expected_core_sha = "148c331da27c1e49eb0d30ab83ff442dce318d91e686fea6ab55917196a59d9c"
actual_core_sha = hashlib.sha256(core_bytes).hexdigest()
if actual_core_sha != expected_core_sha:
    raise SystemExit(f"Bosses r3 core SHA mismatch: {actual_core_sha}")
replacement = core_bytes.decode("utf-8")
text = text[:start] + replacement + "\n      " + text[end:]

required = [
    "HK_BOSSES_CANON_REV='bosses-canon-core-20260920-r1'",
    "HK_BOSSES_TARGET_REV='bosses-area-target-20260920-r2'",
    "HK_BOSSES_CALC_REV='bosses-area-calculator-20260920-r3'",
    "function bossCanonCalcResult",
    "function bossCanonCalculatorHtml",
    "function bossCanonOpenCalculator",
    "function bossCanonRewardDelta",
    "data-boss-calc-open",
    "data-boss-calc-target",
    "data-boss-calc-boss",
]
for needle in required:
    if needle not in text:
        raise SystemExit(f"missing invariant after patch: {needle}")

path.write_text(text, encoding="utf-8")
print("Bosses Area calculator r3 patch applied")
