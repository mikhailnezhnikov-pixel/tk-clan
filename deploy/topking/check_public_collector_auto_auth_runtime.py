#!/usr/bin/env python3
import hashlib
import importlib.util
import json
import os
import re
import sqlite3
import subprocess
import tempfile
import time

DB="/var/lib/hamsterking-license/licenses.db"
IDENTITY="/var/lib/hamsterking-license/public-collector-identity.sha256"
TOKEN="/var/lib/hamsterking-license/public-collector-token"
BOOTSTRAP="/var/lib/hamsterking-license/public-collector-auth.json"
PROBE="/var/lib/hamsterking-license/public-collector-auth-probe.json"
SERVER="/opt/hamsterking-license/server.py"
USERSCRIPT="/opt/hamsterking-license/HamsterKingMobile.user.js"

def yes(v): return "yes" if bool(v) else "no"

def present(path):
    try:
        return os.path.getsize(path)>0
    except OSError:
        return False

try:
    expected=open(IDENTITY,encoding="ascii").read(256).strip()
except OSError:
    expected=""

print("runtime_check_revision=PUBLIC_COLLECTOR_FINAL_AUTH_RUNTIME_R1")
print("identity_present="+yes(expected))
print("token_present="+yes(present(TOKEN)))
print("bootstrap_present="+yes(present(BOOTSTRAP)))
print("probe_file_absent="+yes(not os.path.exists(PROBE)))
if not expected or not present(TOKEN) or not present(BOOTSTRAP) or os.path.exists(PROBE):
    raise SystemExit(2)

# Read service HK_* settings without displaying values.
show=subprocess.check_output(
    ["systemctl","show","hamsterking-license.service","--property=MainPID","--no-pager"],
    text=True,stderr=subprocess.STDOUT,timeout=10,
)
main_pid=next((line.split("=",1)[1].strip() for line in show.splitlines() if line.startswith("MainPID=")),"")
if not main_pid or main_pid=="0":
    raise SystemExit(3)
raw_env=open(f"/proc/{int(main_pid)}/environ","rb").read(2_000_000)
for item in raw_env.split(b"\x00"):
    if not item.startswith(b"HK_") or b"=" not in item:
        continue
    key,value=item.split(b"=",1)
    os.environ[key.decode("utf-8","replace")]=value.decode("utf-8","replace")

# Resolve technical account only by identity digest; never print the account ID.
db=sqlite3.connect(DB)
db.row_factory=sqlite3.Row
now=int(time.time())
rows=db.execute("""
SELECT l.player_id,d.device_id
FROM licenses l
JOIN devices d ON d.player_id=l.player_id
WHERE l.active=1 AND (l.expires_at IS NULL OR l.expires_at>?)
ORDER BY d.last_seen DESC
LIMIT 500
""",(now,)).fetchall()
db.close()
technical=next(
    (row for row in rows if hashlib.sha256(str(row["player_id"]).encode()).hexdigest()==expected),
    None,
)
print("technical_candidate_present="+yes(technical))
if technical is None:
    raise SystemExit(4)

spec=importlib.util.spec_from_file_location("hk_final_runtime",SERVER)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Use a database backup so this eligibility check cannot mutate the real device state.
with tempfile.TemporaryDirectory(prefix="hk-final-auth-") as td:
    temp_db=os.path.join(td,"licenses.db")
    source=sqlite3.connect(DB)
    target=sqlite3.connect(temp_db)
    source.backup(target)
    target.close()
    source.close()
    original_db=mod.DB_PATH
    mod.DB_PATH=temp_db
    try:
        status,doc=mod.license_check(
            str(technical["player_id"]),
            str(technical["device_id"]),
            "1.17.12",
            "127.0.0.1",
        )
    finally:
        mod.DB_PATH=original_db

technical_allowed=(int(status)==200 and isinstance(doc,dict) and bool(doc.get("allowed")))
technical_auth_sync=(technical_allowed and bool(doc.get("public_collector_auth_sync")))
print("technical_check_status="+str(status))
print("technical_allowed="+yes(technical_allowed))
print("technical_auth_sync="+yes(technical_auth_sync))
print("technical_real_license_db_untouched=yes")
if not technical_auth_sync:
    raise SystemExit(5)

server_src=open(SERVER,encoding="utf-8").read()
user_src=open(USERSCRIPT,encoding="utf-8").read()
server_probe_absent=all(marker not in server_src for marker in (
    'path == "/api/v1/public-collector/auth-probe"',
    "def accept_public_collector_auth_probe(",
    "PUBLIC_COLLECTOR_AUTH_PROBE_PATH =",
))
server_sync_i=server_src.find('path == "/api/v1/public-collector/auth-sync"')
server_sync_block=server_src[server_sync_i:server_sync_i+2600] if server_sync_i>=0 else ""
server_guard=server_sync_block.find("public_collector_auth_sync_allowed(player_id)")
server_read=server_sync_block.find("self.read_json(")
server_sync_guard=(server_sync_i>=0 and server_guard>=0 and server_read>=0 and server_guard<server_read)
client_probe_absent=all(marker not in user_src for marker in (
    "const PUBLIC_COLLECTOR_AUTH_PROBE_URL",
    "async function sendPublicCollectorAuthProbe",
    "async function buildPublicCollectorAuthProbe",
    "function safeStorageProbeArea",
))
client_sync_i=user_src.find("async function maybeSyncPublicCollectorAuthorization")
client_sync_block=user_src[client_sync_i:client_sync_i+2400] if client_sync_i>=0 else ""
client_sync_guard=(client_sync_i>=0 and "!licenseState.publicCollectorAuthSync" in client_sync_block)
no_auth_create_regression=(
    "PRELOGIN_ZERO_GAME_API_R1" in user_src
    and "AUTH_PASSIVE_SAFETY_R1" in user_src
)
print("server_probe_runtime_absent="+yes(server_probe_absent))
print("server_sync_identity_guard="+yes(server_sync_guard))
print("client_probe_runtime_absent="+yes(client_probe_absent))
print("client_sync_technical_guard="+yes(client_sync_guard))
print("client_passive_auth_safety="+yes(no_auth_create_regression))
if not all((server_probe_absent,server_sync_guard,client_probe_absent,client_sync_guard,no_auth_create_regression)):
    raise SystemExit(6)

# Search recent service logs for actual secret values, never print those values.
chunks=[]
for unit in ("hamsterking-license.service","hamsterking-public-war.service","hamsterking-public-collector.service"):
    try:
        chunks.append(subprocess.check_output(
            ["journalctl","-u",unit,"--since","24 hours ago","--no-pager"],
            text=True,stderr=subprocess.DEVNULL,timeout=20,
        ))
    except Exception:
        chunks.append("")
journal="\n".join(chunks)
try:
    token_value=open(TOKEN,encoding="utf-8").read().strip()
except OSError:
    token_value=""
try:
    bootstrap=json.load(open(BOOTSTRAP,encoding="utf-8"))
    auth_data_value=str(bootstrap.get("auth_data") or "")
except Exception:
    auth_data_value=""
token_logged=bool(token_value and token_value in journal)
auth_data_logged=bool(auth_data_value and auth_data_value in journal)
bearer_logged=bool(re.search(r"Bearer\s+eyJ[A-Za-z0-9._~-]{20,}",journal,re.I))
print("token_value_logged="+("YES" if token_logged else "NO"))
print("auth_data_logged="+("YES" if auth_data_logged else "NO"))
print("bearer_value_logged="+("YES" if bearer_logged else "NO"))
if token_logged or auth_data_logged or bearer_logged:
    raise SystemExit(7)

print("PUBLIC_COLLECTOR_TECHNICAL_AUTH_SYNC=PASS")
print("PUBLIC_COLLECTOR_LOG_SECRET_AUDIT=PASS")
