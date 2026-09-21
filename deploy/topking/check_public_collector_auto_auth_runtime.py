#!/usr/bin/env python3
import base64
import json
import os
import subprocess
import time

TOKEN_PATH="/var/lib/hamsterking-license/public-collector-token"
AUTH_PATH="/var/lib/hamsterking-license/public-collector-auth.json"
IDENTITY_PATH="/var/lib/hamsterking-license/public-collector-identity.sha256"
REFRESH_PATH="/var/lib/hamsterking-license/public-collector-auth-refresh.json"

def present(path):
    try:
        return os.path.getsize(path)>0
    except OSError:
        return False

print("identity_present="+("yes" if present(IDENTITY_PATH) else "no"))
print("token_present="+("yes" if present(TOKEN_PATH) else "no"))
if present(TOKEN_PATH):
    token=open(TOKEN_PATH,encoding="utf-8").read().strip()
    exp=0
    try:
        part=token.split(".")[1]
        part += "="*(-len(part)%4)
        claims=json.loads(base64.urlsafe_b64decode(part.encode()).decode())
        exp=int(claims.get("exp") or 0)
    except Exception:
        pass
    print("token_exp="+str(exp))
    print("token_seconds_left="+str(exp-int(time.time()) if exp else 0))

print("bootstrap_present="+("yes" if present(AUTH_PATH) else "no"))
if present(AUTH_PATH):
    try:
        doc=json.load(open(AUTH_PATH,encoding="utf-8"))
    except Exception:
        doc={}
    print("bootstrap_auth_type="+str(doc.get("auth_type","")))
    print("bootstrap_platform="+str(doc.get("platform","")))
    print("bootstrap_updated_at="+str(doc.get("updated_at",0)))

print("refresh_backoff_present="+("yes" if os.path.exists(REFRESH_PATH) else "no"))

# Safe check: does the pinned technical identity correspond to a licensed
# player that has checked in recently? Never print the player ID.
try:
    import hashlib, sqlite3
    expected=open(IDENTITY_PATH,encoding="ascii").read().strip() if present(IDENTITY_PATH) else ""
    db=sqlite3.connect("/var/lib/hamsterking-license/licenses.db")
    db.row_factory=sqlite3.Row
    matched=None
    for row in db.execute("SELECT player_id,active,expires_at FROM licenses"):
        digest=hashlib.sha256(str(row["player_id"]).encode()).hexdigest()
        if expected and digest==expected:
            matched=row
            break
    print("technical_license_present="+("yes" if matched else "no"))
    if matched:
        print("technical_license_active="+("yes" if int(matched["active"] or 0)==1 else "no"))
        device=db.execute(
            "SELECT last_seen,script_version FROM devices WHERE player_id=? ORDER BY last_seen DESC LIMIT 1",
            (matched["player_id"],)
        ).fetchone()
        print("technical_last_seen="+str(int(device["last_seen"] or 0) if device else 0))
        print("technical_script_version="+str(device["script_version"] if device else ""))
    db.close()
except Exception as exc:
    print("technical_license_check=unavailable")

# Safe reverse-proxy check: only report whether auth-sync was requested and
# the latest HTTP status/time; never print IP, token, query/body, or User-Agent.
sync_events=[]
for log_path in ("/var/log/nginx/access.log", "/var/log/nginx/access.log.1"):
    try:
        lines=open(log_path,encoding="utf-8",errors="replace").read().splitlines()[-5000:]
    except OSError:
        continue
    for line in lines:
        if "/api/v1/public-collector/auth-sync" not in line:
            continue
        import re
        tm=re.search(r"\[([^\]]+)\]", line)
        st=re.search(r'"\s+(\d{3})\s+', line)
        sync_events.append((tm.group(1) if tm else "", st.group(1) if st else ""))
print("auth_sync_request_seen="+("yes" if sync_events else "no"))
if sync_events:
    print("auth_sync_latest_time="+sync_events[-1][0])
    print("auth_sync_latest_status="+sync_events[-1][1])

for unit,label in (
    ("hamsterking-public-war.service","war_journal"),
    ("hamsterking-public-collector.service","ratings_journal"),
):
    print("=== "+label+" ===")
    try:
        out=subprocess.check_output(
            ["journalctl","-u",unit,"-n","12","--no-pager"],
            text=True,stderr=subprocess.STDOUT,timeout=10,
        )
    except Exception:
        out=""
    for line in out.splitlines():
        if "[public-collector]" in line or "Starting " in line or "Finished " in line:
            print(line)
