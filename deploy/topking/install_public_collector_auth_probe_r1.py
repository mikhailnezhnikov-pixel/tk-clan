#!/usr/bin/env python3
import hashlib, os, shutil, subprocess, sys, time
from pathlib import Path

LIVE=Path("/opt/hamsterking-license/server.py")
CAND=Path("/tmp/server.auth-probe-r1.py")

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

if len(sys.argv)!=2:
    raise SystemExit("usage: installer EXPECTED_SHA")
expected=sys.argv[1].strip()
if not LIVE.exists() or not CAND.exists():
    raise SystemExit("required file missing")
if sha256(LIVE)!=expected:
    print("LIVE_SERVER_CHANGED")
    raise SystemExit(42)

subprocess.check_call([sys.executable,"-m","py_compile",str(CAND)])
stamp=time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(LIVE,LIVE.with_name(LIVE.name+f".bak.auth-probe-r1.{stamp}"))
tmp=LIVE.with_name(LIVE.name+".new")
shutil.copy2(CAND,tmp)
os.chmod(tmp,0o644)
os.replace(tmp,LIVE)
subprocess.check_call(["systemctl","restart","hamsterking-license.service"])
subprocess.check_call(["systemctl","is-active","--quiet","hamsterking-license.service"])
print("public_collector_auth_probe_install=PASS")
print("live_sha="+sha256(LIVE))
