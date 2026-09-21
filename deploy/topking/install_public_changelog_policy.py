#!/usr/bin/env python3
import hashlib
import os
import shutil
import sys
import time
from pathlib import Path

LIVE_USER = Path("/opt/hamsterking-license/HamsterKingMobile.user.js")
LIVE_SERVER = Path("/opt/hamsterking-license/server.py")
CAND_USER = Path("/tmp/HamsterKingMobile.public-changelog.user.js")
CAND_SERVER = Path("/tmp/server.public-changelog.py")

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

if len(sys.argv) != 3:
    raise SystemExit("usage: install_public_changelog_policy.py EXPECTED_USER_SHA EXPECTED_SERVER_SHA")

expected_user, expected_server = sys.argv[1].strip(), sys.argv[2].strip()
for path in (LIVE_USER, LIVE_SERVER, CAND_USER, CAND_SERVER):
    if not path.exists():
        raise SystemExit(f"missing required file: {path}")

if sha256(LIVE_USER) != expected_user:
    raise SystemExit("LIVE_USERSCRIPT_CHANGED")
if sha256(LIVE_SERVER) != expected_server:
    raise SystemExit("LIVE_SERVER_CHANGED")

stamp = time.strftime("%Y%m%d-%H%M%S")
backup_user = LIVE_USER.with_name(LIVE_USER.name + f".bak.public-changelog.{stamp}")
backup_server = LIVE_SERVER.with_name(LIVE_SERVER.name + f".bak.public-changelog.{stamp}")
shutil.copy2(LIVE_USER, backup_user)
shutil.copy2(LIVE_SERVER, backup_server)

tmp_user = LIVE_USER.with_name(LIVE_USER.name + ".new")
tmp_server = LIVE_SERVER.with_name(LIVE_SERVER.name + ".new")
shutil.copy2(CAND_USER, tmp_user)
shutil.copy2(CAND_SERVER, tmp_server)
os.chmod(tmp_user, LIVE_USER.stat().st_mode & 0o777)
os.chmod(tmp_server, LIVE_SERVER.stat().st_mode & 0o777)
os.replace(tmp_user, LIVE_USER)
os.replace(tmp_server, LIVE_SERVER)

print("PUBLIC_CHANGELOG_POLICY_INSTALL=PASS")
print("userscript_sha=" + sha256(LIVE_USER))
print("server_sha=" + sha256(LIVE_SERVER))
print("backup_user=" + str(backup_user))
print("backup_server=" + str(backup_server))
