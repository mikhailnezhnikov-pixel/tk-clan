from pathlib import Path
import hashlib

LIVE = Path("/tmp/HamsterKingMobile.user.js")
BASELINE = Path("baseline/topking/HamsterKingMobile.current.user.js")
CANDIDATE = Path("deploy/topking/HamsterKingMobile.1.17.44.generals-kokkaras-cost-parity.candidate.user.js")

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

live = LIVE.read_bytes()
baseline = BASELINE.read_bytes()
candidate = CANDIDATE.read_bytes()

if live != baseline:
    raise SystemExit(
        f"GENERALS_1_17_44_SOURCE_MISMATCH live={sha256(live)} baseline={sha256(baseline)}"
    )

live_text = live.decode("utf-8")
candidate_text = candidate.decode("utf-8")

required_source = [
    "// @version      1.17.43",
    "const BUILD_VERSION = '1.17.43';",
    "hamsters-kokkaras-auth-state-20260923-r3",
    "treasure-guide-selective-extract-20260923-r2",
    "maps-manual-scan-only-20260923-r1",
    "public-collector-activity-lease-20260922-r1",
]
for marker in required_source:
    if marker not in live_text:
        raise SystemExit("GENERALS_1_17_44_SOURCE_MARKER_MISSING: " + marker)

required_candidate = [
    "// @version      1.17.44",
    "const BUILD_VERSION = '1.17.44';",
    "generals-kokkaras-cost-parity-20260923-r1",
    "hamsters-kokkaras-auth-state-20260923-r3",
    "treasure-guide-selective-extract-20260923-r2",
    "maps-manual-scan-only-20260923-r1",
    "public-collector-activity-lease-20260922-r1",
    "HK_PUBLIC_SNAPSHOT_CLIENT_REV = 'public-server-only-20260920-r2'",
    "HK_EXPLORE_CANON_REV='explore-e3-single-20260920-r9-runner'",
    "const HK_MAP_READ_CONCURRENCY = 5;",
    "function growthGeneralCostSafe(cost){ return growthSafeCost(cost)&&growthPitCost(cost)>0&&growthNutCost(cost)>0; }",
    "box.classList.toggle('generals-run',generalsRun)",
]
for marker in required_candidate:
    if marker not in candidate_text:
        raise SystemExit("GENERALS_1_17_44_CANDIDATE_MARKER_MISSING: " + marker)

if candidate_text.count("submitOwnedMapAreas(true)") != 1:
    raise SystemExit("GENERALS_1_17_44_MAPS_INVARIANT_FAILED")
if candidate_text.count("collectPublicSnapshot(") != 1:
    raise SystemExit("GENERALS_1_17_44_PUBLIC_SNAPSHOT_INVARIANT_FAILED")
if "setInterval(() => collectPublicSnapshot()" in candidate_text:
    raise SystemExit("GENERALS_1_17_44_CLIENT_COLLECTOR_REGRESSION")

LIVE.write_bytes(candidate)
print("GENERALS_1_17_44_TRANSPORT_PATCH=PASS")
print("source_sha256=" + sha256(live))
print("candidate_sha256=" + sha256(candidate))
