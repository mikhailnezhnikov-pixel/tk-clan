from pathlib import Path
import base64, zlib, hashlib

path = Path("/tmp/HamsterKingMobile.user.js")
text = path.read_text(encoding="utf-8")

old_outer = "const HK_STAGE2J_BOSSES_REV = 'bosses-canon-core-20260920-r1';"
new_outer = "const HK_STAGE2J_BOSSES_REV = 'bosses-area-target-20260920-r2';"
if text.count(old_outer) != 1:
    raise SystemExit(f"expected exactly one Bosses r1 outer marker, got {text.count(old_outer)}")
text = text.replace(old_outer, new_outer, 1)

part_paths = [
    Path("deploy/topking/bosses-r2-payload-0.txt"),
    Path("deploy/topking/bosses-r2-payload-1.txt"),
    Path("deploy/topking/bosses-r2-payload-2.txt"),
    Path("deploy/topking/bosses-r2-payload-3.txt"),
]
parts = [p.read_text(encoding="utf-8").strip() for p in part_paths]
if not all(parts):
    raise SystemExit("empty Bosses r2 payload part")
payload_text = "".join(parts)

try:
    compressed = base64.b64decode(payload_text, validate=True)
except Exception as exc:
    raise SystemExit(f"Bosses r2 base64 invalid: {exc}")

try:
    core_bytes = zlib.decompress(compressed)
except Exception as exc:
    raise SystemExit(f"Bosses r2 zlib invalid: {exc}")

core = core_bytes.decode("utf-8")
old_inner = "HK_BOSSES_CANON_REV='bosses-canon-core-20260920-r1'"
new_inner = "HK_BOSSES_CANON_REV='bosses-area-target-20260920-r2'"
if core.count(old_inner) != 1:
    raise SystemExit(f"expected exactly one Bosses r1 inner marker in payload, got {core.count(old_inner)}")
core = core.replace(old_inner, new_inner, 1)

required_core = [
    "HK_BOSSES_CANON_REV='bosses-area-target-20260920-r2'",
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
for needle in required_core:
    if needle not in core:
        raise SystemExit(f"missing Bosses r2 core invariant: {needle}")

core_sha = hashlib.sha256(core.encode("utf-8")).hexdigest()

start_anchor = "  function bossStateRows(documentValue = bossSnapshot || hkStateStore.snapshot || playerDocument) {"
end_anchor = "      function renderWars() {"
start = text.find(start_anchor)
end = text.find(end_anchor, start)
if start < 0 or end < 0 or end <= start:
    raise SystemExit("Bosses core block anchors not found")

text = text[:start] + core + "\n      " + text[end:]

required_final = [
    "HK_STAGE2J_BOSSES_REV = 'bosses-area-target-20260920-r2'",
    "HK_BOSSES_CANON_REV='bosses-area-target-20260920-r2'",
    "HK_BOSSES_TARGET_REV='bosses-area-target-20260920-r2'",
    "function bossCanonTargetPlan",
    "function bossCanonRewardOnlyPlan",
    "async function bossCanonRunAreaTargetContinuation",
]
for needle in required_final:
    if needle not in text:
        raise SystemExit(f"missing Bosses r2 final invariant: {needle}")

path.write_text(text, encoding="utf-8")
print(f"BOSSES_R2_CORE_SHA={core_sha}")
print(f"BOSSES_R2_PATCHED_SHA={hashlib.sha256(text.encode('utf-8')).hexdigest()}")
print("Bosses Area target r2 patch applied")
