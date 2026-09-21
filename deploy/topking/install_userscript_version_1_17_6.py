#!/usr/bin/env python3
import hashlib
import os
import shutil
import sys
import time
from pathlib import Path

LIVE = Path("/opt/hamsterking-license/HamsterKingMobile.user.js")
CANDIDATE = Path("/tmp/HamsterKingMobile.1.17.6.user.js")

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: installer.py EXPECTED_LIVE_SHA")
    expected=sys.argv[1].strip()
    if not LIVE.exists() or not CANDIDATE.exists():
        raise SystemExit("required file missing")
    if sha256(LIVE)!=expected:
        print("LIVE_USERSCRIPT_CHANGED")
        return 43
    stamp=time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(LIVE, LIVE.with_name(LIVE.name+f".bak.1.17.6.{stamp}"))
    tmp=LIVE.with_name(LIVE.name+".new")
    shutil.copy2(CANDIDATE,tmp)
    os.chmod(tmp,0o644)
    os.replace(tmp,LIVE)
    print("userscript_1_17_6_install=PASS")
    print("live_sha="+sha256(LIVE))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
