#!/usr/bin/env python3
import hashlib
import importlib.util
import json
import os
import sqlite3
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

DB="/var/lib/hamsterking-license/licenses.db"
IDENTITY="/var/lib/hamsterking-license/public-collector-identity.sha256"
BASE="http://127.0.0.1:3188"
HOST="hk-license.89.125.1.71.sslip.io"
ORIGIN="https://app.hamsterking.games"

def yes(v): return "yes" if bool(v) else "no"

try:
    expected=open(IDENTITY,encoding="ascii").read(256).strip()
except OSError:
    expected=""
print("technical_identity_present="+yes(expected))
if not expected:
    raise SystemExit(2)

db=sqlite3.connect(DB)
db.row_factory=sqlite3.Row
now=int(time.time())
rows=db.execute("""
SELECT l.player_id,l.expires_at,d.device_id,d.script_version,d.last_seen
FROM licenses l
JOIN devices d ON d.player_id=l.player_id
WHERE l.active=1 AND (l.expires_at IS NULL OR l.expires_at>?)
ORDER BY d.last_seen DESC
LIMIT 500
""",(now,)).fetchall()
db.close()

technical=None
for row in rows:
    if hashlib.sha256(str(row["player_id"]).encode()).hexdigest()==expected:
        technical=row
        break
print("technical_candidate_present="+yes(technical))
if technical is None:
    raise SystemExit(3)

show=subprocess.check_output(
    ["systemctl","show","hamsterking-license.service","--property=MainPID","--no-pager"],
    text=True,stderr=subprocess.STDOUT,timeout=10,
)
main_pid=next((line.split("=",1)[1].strip() for line in show.splitlines() if line.startswith("MainPID=")),"")
if not main_pid or main_pid=="0":
    raise SystemExit(4)
raw_env=open(f"/proc/{int(main_pid)}/environ","rb").read(2_000_000)
for item in raw_env.split(b"\x00"):
    if not item.startswith(b"HK_") or b"=" not in item:
        continue
    key,value=item.split(b"=",1)
    os.environ[key.decode("utf-8","replace")]=value.decode("utf-8","replace")

spec=importlib.util.spec_from_file_location("hk_contract_live","/opt/hamsterking-license/server.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory(prefix="hk-contract-") as td:
    temp_db=os.path.join(td,"licenses.db")
    source=sqlite3.connect(DB)
    target=sqlite3.connect(temp_db)
    source.backup(target)
    target.close()
    source.close()
    real_db_path=mod.DB_PATH
    mod.DB_PATH=temp_db
    try:
        status,doc=mod.license_check(
            str(technical["player_id"]),
            str(technical["device_id"]),
            "1.17.12",
            "127.0.0.1",
        )
    finally:
        mod.DB_PATH=real_db_path

license_token=str(doc.get("token") or "") if isinstance(doc,dict) else ""
allowed=bool(doc.get("allowed")) if isinstance(doc,dict) else False
auth_sync=bool(doc.get("public_collector_auth_sync")) if isinstance(doc,dict) else False
print("technical_check_status="+str(status))
print("technical_check_allowed="+yes(allowed))
print("technical_check_token_present="+yes(license_token))
print("technical_check_auth_sync="+yes(auth_sync))
print("technical_real_license_db_untouched=yes")
if int(status)!=200 or not allowed or not license_token or not auth_sync:
    raise SystemExit(5)

def post(path,body,token=""):
    data=json.dumps(body,separators=(",",":")).encode("utf-8")
    headers={
        "Content-Type":"application/json",
        "Accept":"application/json",
        "Origin":ORIGIN,
        "Host":HOST,
        "User-Agent":"TopKing-Collector-Contract-Test/1",
    }
    if token:
        headers["Authorization"]="Bearer "+token
    req=urllib.request.Request(BASE+path,data=data,headers=headers,method="POST")
    try:
        with urllib.request.urlopen(req,timeout=15) as resp:
            raw=resp.read(200000)
            try: body=json.loads(raw.decode("utf-8"))
            except Exception: body={}
            return int(resp.status),body
    except urllib.error.HTTPError as exc:
        raw=exc.read(200000)
        try: body=json.loads(raw.decode("utf-8"))
        except Exception: body={}
        return int(exc.code),body

probe_status,_=post("/api/v1/public-collector/auth-probe",{},license_token)
sync_status,sync_doc=post("/api/v1/public-collector/auth-sync",{},license_token)
probe_removed=(probe_status in (404,405))
sync_reached_after_identity=(sync_status==400 and isinstance(sync_doc,dict) and sync_doc.get("error")=="invalid_collector_auth")
print("technical_probe_status="+str(probe_status))
print("technical_probe_route_removed="+yes(probe_removed))
print("technical_sync_empty_status="+str(sync_status))
print("technical_sync_passed_identity_guard="+yes(sync_reached_after_identity))
if not probe_removed or not sync_reached_after_identity:
    raise SystemExit(6)

src=open("/opt/hamsterking-license/server.py",encoding="utf-8").read()
probe_absent=all(marker not in src for marker in (
    'path == "/api/v1/public-collector/auth-probe"',
    "def accept_public_collector_auth_probe(",
    "PUBLIC_COLLECTOR_AUTH_PROBE_PATH =",
))
sync_i=src.find('path == "/api/v1/public-collector/auth-sync"')
sync_block=src[sync_i:sync_i+2600] if sync_i>=0 else ""
guard=sync_block.find("public_collector_auth_sync_allowed(player_id)")
read=sync_block.find("self.read_json(")
sync_guard_ok=(sync_i>=0 and guard>=0 and read>=0 and guard<read)
print("technical_probe_static_absent="+yes(probe_absent))
print("technical_sync_identity_guard_before_body="+yes(sync_guard_ok))
if not probe_absent or not sync_guard_ok:
    raise SystemExit(7)

print("PUBLIC_COLLECTOR_TECHNICAL_AUTH_SYNC=PASS")
