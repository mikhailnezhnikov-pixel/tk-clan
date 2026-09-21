#!/usr/bin/env python3
import hashlib
import json
import os
import sqlite3
import time
import urllib.error
import urllib.request

DB="/var/lib/hamsterking-license/licenses.db"
IDENTITY="/var/lib/hamsterking-license/public-collector-identity.sha256"
BASE="http://127.0.0.1:3188"
HOST="hk-license.89.125.1.71.sslip.io"
ORIGIN="https://app.hamsterking.games"

def yes(v): return "yes" if bool(v) else "no"

expected=""
try:
    expected=open(IDENTITY,encoding="ascii").read(256).strip()
except OSError:
    pass

db=sqlite3.connect(DB)
db.row_factory=sqlite3.Row
now=int(time.time())
rows=db.execute("""
SELECT l.player_id,l.expires_at,d.device_id,d.script_version,d.last_seen
FROM licenses l
JOIN devices d ON d.player_id=l.player_id
WHERE l.active=1 AND (l.expires_at IS NULL OR l.expires_at>?)
ORDER BY d.last_seen DESC
LIMIT 200
""",(now,)).fetchall()
db.close()

candidate=None
for row in rows:
    digest=hashlib.sha256(str(row["player_id"]).encode()).hexdigest()
    if expected and digest==expected:
        continue
    version=str(row["script_version"] or "").strip()
    if not version:
        continue
    candidate=row
    break

print("isolation_test_revision=PUBLIC_COLLECTOR_NORMAL_PLAYER_ISOLATION_R1")
print("normal_candidate_present="+yes(candidate))
if candidate is None:
    raise SystemExit(2)

def post(path,body,token=""):
    data=json.dumps(body,separators=(",",":")).encode("utf-8")
    headers={
        "Content-Type":"application/json",
        "Accept":"application/json",
        "Origin":ORIGIN,
        "Host":HOST,
        "User-Agent":"TopKing-Collector-Isolation-Test/1",
    }
    if token:
        headers["Authorization"]="Bearer "+token
    req=urllib.request.Request(BASE+path,data=data,headers=headers,method="POST")
    try:
        with urllib.request.urlopen(req,timeout=15) as resp:
            raw=resp.read(200000)
            try: doc=json.loads(raw.decode("utf-8"))
            except Exception: doc={}
            return int(resp.status),doc
    except urllib.error.HTTPError as exc:
        raw=exc.read(200000)
        try: doc=json.loads(raw.decode("utf-8"))
        except Exception: doc={}
        return int(exc.code),doc

check_status,check_doc=post("/api/v1/check",{
    "player_id":str(candidate["player_id"]),
    "device_id":str(candidate["device_id"]),
    "script_version":str(candidate["script_version"]),
})
license_token=str(check_doc.get("token") or "") if isinstance(check_doc,dict) else ""
allowed=bool(check_doc.get("allowed")) if isinstance(check_doc,dict) else False
auth_sync=bool(check_doc.get("public_collector_auth_sync")) if isinstance(check_doc,dict) else False
print("normal_check_status="+str(check_status))
print("normal_check_allowed="+yes(allowed))
print("normal_check_token_present="+yes(license_token))
print("normal_check_auth_sync="+yes(auth_sync))

if check_status!=200 or not allowed or not license_token or auth_sync:
    raise SystemExit(3)

probe_status,probe_doc=post("/api/v1/public-collector/auth-probe",{},license_token)
sync_status,sync_doc=post("/api/v1/public-collector/auth-sync",{},license_token)
print("normal_probe_status="+str(probe_status))
print("normal_probe_identity_denied="+yes(probe_status==403 and isinstance(probe_doc,dict) and probe_doc.get("error")=="collector_identity_not_allowed"))
print("normal_sync_status="+str(sync_status))
print("normal_sync_identity_denied="+yes(sync_status==403 and isinstance(sync_doc,dict) and sync_doc.get("error")=="collector_identity_not_allowed"))

if probe_status!=403 or sync_status!=403:
    raise SystemExit(4)
if probe_doc.get("error")!="collector_identity_not_allowed" or sync_doc.get("error")!="collector_identity_not_allowed":
    raise SystemExit(5)

# Static live-source regression guard: both routes must check the identity
# before reading their request bodies.
src=open("/opt/hamsterking-license/server.py",encoding="utf-8").read()
for route in ("/api/v1/public-collector/auth-probe","/api/v1/public-collector/auth-sync"):
    i=src.find('path == "'+route+'"')
    if i<0:
        raise SystemExit(6)
    block=src[i:i+2400]
    guard=block.find("public_collector_auth_sync_allowed(player_id)")
    read=block.find("self.read_json(")
    ok=(guard>=0 and read>=0 and guard<read)
    print(("probe" if route.endswith("auth-probe") else "sync")+"_identity_guard_before_body="+yes(ok))
    if not ok:
        raise SystemExit(7)

print("PUBLIC_COLLECTOR_NORMAL_PLAYER_ISOLATION=PASS")
