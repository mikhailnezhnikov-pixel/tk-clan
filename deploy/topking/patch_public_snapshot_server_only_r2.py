from pathlib import Path
p=Path("/tmp/HamsterKingMobile.user.js")
s=p.read_text()

old_rev="const HK_PUBLIC_SNAPSHOT_CLIENT_REV = 'public-snapshot-3h-20260920-r1';"
new_rev="const HK_PUBLIC_SNAPSHOT_CLIENT_REV = 'public-server-only-20260920-r2';"
assert s.count(old_rev)==1, s.count(old_rev)
s=s.replace(old_rev,new_rev,1)

old="""  async function collectPublicSnapshot(force = false) {
    if (publicSnapshotPromise || !licenseState.allowed || !licenseState.token || !apiHeaders.Authorization) return publicSnapshotPromise;
    if (!force && Date.now() - lastPublicSnapshot < PUBLIC_SNAPSHOT_INTERVAL_MS) return null;
    publicSnapshotPromise = (async () => {
      try {
        const [warResult, ratings] = await Promise.all([readPublicWarV4(), readPublicRatingsV4()]);
        const payload = {ratings}; if (warResult.read) payload.war = warResult.war;
        if (!warResult.read && !Object.keys(ratings).length) return;
        await publicSnapshotServerJson(payload); lastPublicSnapshot = Date.now();
      } catch (error) { console.warn('[HK] public snapshot failed', error); }
      finally { publicSnapshotPromise = null; }
    })();
    return publicSnapshotPromise;
  }

"""
new="""  async function collectPublicSnapshot(force = false) {
    recordDiagnostic('public-snapshot-server-only',{force:!!force,revision:HK_PUBLIC_SNAPSHOT_CLIENT_REV});
    return null;
  }

"""
assert s.count(old)==1, s.count(old)
s=s.replace(old,new,1)

call="    setInterval(() => collectPublicSnapshot(), PUBLIC_SNAPSHOT_INTERVAL_MS);\n"
assert s.count(call)==1, s.count(call)
s=s.replace(call,"",1)

assert s.count("collectPublicSnapshot(")==1
assert "Promise.all([readPublicWarV4(), readPublicRatingsV4()])" not in s[s.index("  async function collectPublicSnapshot"):s.index("  async function loadFair")]
assert "HK_EXPLORE_CANON_REV='explore-e3-single-20260920-r9-runner'" in s
assert "const HK_MAP_READ_CONCURRENCY = 5;" in s

p.write_text(s)
