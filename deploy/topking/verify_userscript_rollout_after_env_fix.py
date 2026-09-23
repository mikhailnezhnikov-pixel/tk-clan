import importlib.util
import json
import sqlite3
import time
from pathlib import Path

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server_rollout_verify",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

latest=server.release_version()
minimum=server.MIN_SCRIPT_VERSION
print("RELEASE_VERSION",latest)
print("MIN_SCRIPT_VERSION",minimum)

results=[]
for version in ["1.17.24","1.17.81",latest]:
    manifest=server.release_manifest(version,"VERIFY_TOKEN")
    results.append({
        "version":version,
        "latest_version":manifest.get("latest_version"),
        "minimum_version":manifest.get("minimum_version"),
        "available":bool(manifest.get("available")),
        "required":bool(manifest.get("required")),
        "has_download_url":bool(manifest.get("download_url")),
    })
print("MANIFESTS",json.dumps(results,ensure_ascii=False))

assert minimum==latest, (minimum,latest)
for row in results[:-1]:
    assert row["latest_version"]==latest,row
    assert row["minimum_version"]==latest,row
    assert row["available"] is True,row
    assert row["required"] is True,row
    assert row["has_download_url"] is True,row
current=results[-1]
assert current["version"]==latest,current
assert current["available"] is False,current
assert current["required"] is False,current

db=sqlite3.connect(str(server.DB_PATH))
db.row_factory=sqlite3.Row
now=int(time.time())

versions=[]
try:
    rows=db.execute("""SELECT script_version,COUNT(*) AS devices,MAX(last_seen) AS last_seen
                       FROM devices
                       GROUP BY script_version
                       ORDER BY last_seen DESC
                       LIMIT 30""").fetchall()
    for r in rows:
        item=dict(r)
        item["age_s"]=now-int(item.get("last_seen") or 0)
        versions.append(item)
except Exception as exc:
    print("DEVICE_VERSION_QUERY_ERROR",type(exc).__name__,str(exc)[:300])

print("DEVICE_VERSIONS",json.dumps(versions,ensure_ascii=False))
print("ACTIVE_LATEST_DEVICES",sum(int(x.get("devices") or 0) for x in versions if x.get("script_version")==latest))

smoke_rows=0
smoke_latest=0
try:
    smoke_rows=int(db.execute("SELECT COUNT(*) FROM runtime_smoke_captures").fetchone()[0])
    smoke_latest=int(db.execute("SELECT COUNT(*) FROM runtime_smoke_captures WHERE script_version=?",(latest,)).fetchone()[0])
except Exception as exc:
    print("RUNTIME_SMOKE_QUERY_ERROR",type(exc).__name__,str(exc)[:300])

print("RUNTIME_SMOKE_ROWS",smoke_rows)
print("RUNTIME_SMOKE_LATEST_ROWS",smoke_latest)
print("USERSCRIPT_ROLLOUT_VERIFY=PASS")
