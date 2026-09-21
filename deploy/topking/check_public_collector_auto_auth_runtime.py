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
