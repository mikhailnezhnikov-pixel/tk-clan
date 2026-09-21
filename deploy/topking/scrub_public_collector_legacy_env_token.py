#!/usr/bin/env python3
import hashlib
import os
import shutil
import stat
import subprocess
import sys
import tempfile

ENV="/etc/hamsterking-public-collector.env"
COLLECTOR="/opt/hamsterking-license/public_collector.py"
TOKEN="/var/lib/hamsterking-license/public-collector-token"
BOOTSTRAP="/var/lib/hamsterking-license/public-collector-auth.json"
KEY="HK_PUBLIC_COLLECTOR_GAME_TOKEN"

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def key_present():
    try:
        lines=open(ENV,encoding="utf-8").read().splitlines()
    except OSError:
        return False
    for line in lines:
        stripped=line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            continue
        if line.split("=",1)[0].strip()==KEY:
            return True
    return False

if len(sys.argv)!=2:
    raise SystemExit("usage: scrub EXPECTED_ENV_SHA")
expected=sys.argv[1].strip()
if sha256(ENV)!=expected:
    print("LIVE_COLLECTOR_ENV_CHANGED")
    raise SystemExit(42)

collector_src=open(COLLECTOR,encoding="utf-8").read()
if "PUBLIC_COLLECTOR_BOOTSTRAP_SELF_HEAL_R1" not in collector_src:
    raise SystemExit("collector self-heal marker missing")
if not os.path.exists(TOKEN) or os.path.getsize(TOKEN)<=0:
    raise SystemExit("collector token file missing")
if not os.path.exists(BOOTSTRAP) or os.path.getsize(BOOTSTRAP)<=0:
    raise SystemExit("collector bootstrap file missing")

print("legacy_static_token_key_before="+("yes" if key_present() else "no"))

st=os.stat(ENV)
lines=open(ENV,encoding="utf-8").read().splitlines()
kept=[]
removed=0
for line in lines:
    stripped=line.strip()
    if stripped and not stripped.startswith("#") and "=" in line and line.split("=",1)[0].strip()==KEY:
        removed+=1
        continue
    kept.append(line)

rollback=f"/root/.hk-collector-env-rollback-{os.getpid()}"
shutil.copy2(ENV,rollback)
os.chmod(rollback,0o600)
try:
    tmp=ENV+".new"
    with open(tmp,"w",encoding="utf-8") as f:
        f.write("\n".join(kept)+"\n")
    os.chown(tmp,st.st_uid,st.st_gid)
    os.chmod(tmp,0o600)
    os.replace(tmp,ENV)

    subprocess.check_call(["systemctl","start","hamsterking-public-war.service"])
    result=subprocess.check_output(
        ["systemctl","show","hamsterking-public-war.service","-p","Result","--value"],
        text=True,timeout=10,
    ).strip()
    exit_status=subprocess.check_output(
        ["systemctl","show","hamsterking-public-war.service","-p","ExecMainStatus","--value"],
        text=True,timeout=10,
    ).strip()
    if result!="success" or exit_status!="0":
        raise RuntimeError("war collector verification failed")

    mode=stat.S_IMODE(os.stat(ENV).st_mode)
    if key_present():
        raise RuntimeError("legacy token key still present")
    if mode!=0o600:
        raise RuntimeError("collector env mode is not private")
except Exception:
    shutil.copy2(rollback,ENV)
    os.chown(ENV,st.st_uid,st.st_gid)
    os.chmod(ENV,stat.S_IMODE(st.st_mode))
    print("legacy_static_token_scrub_rollback=yes")
    raise
finally:
    try:
        os.unlink(rollback)
    except OSError:
        pass

print("legacy_static_token_lines_removed="+str(removed))
print("legacy_static_token_key_after=no")
print("collector_env_mode_private=yes")
print("war_after_env_scrub=PASS")
print("PUBLIC_COLLECTOR_LEGACY_ENV_TOKEN_REMOVAL=PASS")
