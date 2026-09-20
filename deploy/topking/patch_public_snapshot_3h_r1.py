from pathlib import Path

p=Path("/tmp/HamsterKingMobile.user.js")
s=p.read_text()

old_interval="const PUBLIC_SNAPSHOT_INTERVAL_MS = 15 * 60 * 1000;"
new_interval="const PUBLIC_SNAPSHOT_INTERVAL_MS = 3 * 60 * 60 * 1000;"
assert s.count(old_interval)==1, s.count(old_interval)
s=s.replace(old_interval,new_interval,1)

api_marker="  const PUBLIC_SNAPSHOT_API = 'https://hk-license.89.125.1.71.sslip.io/api/v1/public-snapshot';"
assert s.count(api_marker)==1, s.count(api_marker)
if "HK_PUBLIC_SNAPSHOT_CLIENT_REV" not in s:
    s=s.replace(api_marker,api_marker+"\n  const HK_PUBLIC_SNAPSHOT_CLIENT_REV = 'public-snapshot-3h-20260920-r1';",1)

old_license="""        synchronizeSettings(); flushPitObservations(); loadSharedPitPowers(); refreshSharedClanSkills(); maybeAutoScanClanSkills(); collectPublicSnapshot();"""
new_license="""        synchronizeSettings(); flushPitObservations(); loadSharedPitPowers(); refreshSharedClanSkills(); maybeAutoScanClanSkills();"""
assert s.count(old_license)==1, s.count(old_license)
s=s.replace(old_license,new_license,1)

old_start="""    setTimeout(() => collectPublicSnapshot(true), 5000);
    setInterval(() => collectPublicSnapshot(), PUBLIC_SNAPSHOT_INTERVAL_MS);
"""
new_start="""    setInterval(() => collectPublicSnapshot(), PUBLIC_SNAPSHOT_INTERVAL_MS);
"""
assert s.count(old_start)==1, s.count(old_start)
s=s.replace(old_start,new_start,1)

assert "const PUBLIC_SNAPSHOT_INTERVAL_MS = 3 * 60 * 60 * 1000;" in s
assert "HK_PUBLIC_SNAPSHOT_CLIENT_REV = 'public-snapshot-3h-20260920-r1'" in s
assert "setTimeout(() => collectPublicSnapshot(true), 5000)" not in s
assert "maybeAutoScanClanSkills(); collectPublicSnapshot();" not in s
assert s.count("setInterval(() => collectPublicSnapshot(), PUBLIC_SNAPSHOT_INTERVAL_MS);")==1
assert "HK_EXPLORE_CANON_REV='explore-e3-single-20260920-r9-runner'" in s
assert "const HK_MAP_READ_CONCURRENCY = 5;" in s

p.write_text(s)
