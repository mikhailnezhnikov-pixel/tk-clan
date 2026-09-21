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
