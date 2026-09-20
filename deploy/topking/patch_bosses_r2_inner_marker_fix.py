from pathlib import Path
import hashlib

path = Path("/tmp/HamsterKingMobile.user.js")
text = path.read_text(encoding="utf-8")

required_before = [
    "HK_STAGE2J_BOSSES_REV = 'bosses-area-target-20260920-r2'",
    "HK_BOSSES_TARGET_REV='bosses-area-target-20260920-r2'",
    "function bossCanonTargetPlan",
    "function bossCanonRewardOnlyPlan",
    "async function bossCanonRunAreaTargetContinuation",
]
for needle in required_before:
    if needle not in text:
        raise SystemExit(f"missing pre-fix invariant: {needle}")

old = "HK_BOSSES_CANON_REV='bosses-canon-core-20260920-r1'"
new = "HK_BOSSES_CANON_REV='bosses-area-target-20260920-r2'"
if text.count(old) != 1:
    raise SystemExit(f"expected exactly one stale inner marker, got {text.count(old)}")
if new in text:
    raise SystemExit("r2 inner marker already present before fix")

text = text.replace(old, new, 1)

required_after = required_before + [new]
for needle in required_after:
    if needle not in text:
        raise SystemExit(f"missing post-fix invariant: {needle}")

path.write_text(text, encoding="utf-8")
print("BOSSES_R2_MARKER_FIX_SHA=" + hashlib.sha256(text.encode("utf-8")).hexdigest())
print("Bosses r2 inner marker fixed")
