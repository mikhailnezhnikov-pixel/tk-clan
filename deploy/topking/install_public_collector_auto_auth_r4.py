#!/usr/bin/env python3
import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

LIVE_SERVER = Path("/opt/hamsterking-license/server.py")
LIVE_USER = Path("/opt/hamsterking-license/HamsterKingMobile.user.js")
LIVE_COLLECTOR = Path("/opt/hamsterking-license/public_collector.py")

CAND_SERVER = Path("/tmp/server.auto-auth-r4.py")
CAND_USER = Path("/tmp/HamsterKingMobile.auto-auth-r4.user.js")
CAND_COLLECTOR = Path("/tmp/public_collector.r4.py")

ENV_PATH = Path("/etc/hamsterking-public-collector.env")
TOKEN_PATH = Path("/var/lib/hamsterking-license/public-collector-token")
BOOTSTRAP_PATH = Path("/var/lib/hamsterking-license/public-collector-auth.json")
IDENTITY_PATH = Path("/var/lib/hamsterking-license/public-collector-identity.sha256")
REFRESH_STATUS_PATH = Path("/var/lib/hamsterking-license/public-collector-auth-refresh.json")

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def atomic_install(src: Path, dst: Path, mode: int) -> None:
    tmp = dst.with_name(dst.name + ".new")
    shutil.copy2(src, tmp)
    os.chmod(tmp, mode)
    os.replace(tmp, dst)

def read_env(path: Path) -> dict:
    result = {}
    if not path.exists():
        return result
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        result[k.strip()] = v.strip()
    return result

def ensure_env_lines(path: Path, additions: dict) -> None:
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    present = {line.split("=", 1)[0].strip() for line in lines if "=" in line and not line.lstrip().startswith("#")}
    changed = False
    for key, value in additions.items():
        if key not in present:
            lines.append(f"{key}={value}")
            changed = True
    if changed or not path.exists():
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    else:
        os.chmod(path, 0o600)

def seed_token_file() -> None:
    if TOKEN_PATH.exists() and TOKEN_PATH.stat().st_size > 0:
        os.chmod(TOKEN_PATH, 0o600)
        return
    env = read_env(ENV_PATH)
    token = env.get("HK_PUBLIC_COLLECTOR_GAME_TOKEN", "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token:
        return
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = TOKEN_PATH.with_name(TOKEN_PATH.name + ".tmp")
    tmp.write_text(token + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, TOKEN_PATH)

def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: installer.py SERVER_SOURCE_SHA USERSCRIPT_SOURCE_SHA")
    expected_server, expected_user = sys.argv[1], sys.argv[2]

    for path in (LIVE_SERVER, LIVE_USER, CAND_SERVER, CAND_USER, CAND_COLLECTOR, IDENTITY_PATH):
        if not path.exists():
            raise SystemExit(f"required file missing: {path}")

    if sha256(LIVE_SERVER) != expected_server:
        print("LIVE_SERVER_CHANGED")
        return 42
    if sha256(LIVE_USER) != expected_user:
        print("LIVE_USERSCRIPT_CHANGED")
        return 43

    subprocess.check_call([sys.executable, "-m", "py_compile", str(CAND_SERVER), str(CAND_COLLECTOR)])
    subprocess.check_call(["node", "--check", str(CAND_USER)])

    stamp = time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(LIVE_SERVER, LIVE_SERVER.with_name(LIVE_SERVER.name + f".bak.public-auto-auth-r4.{stamp}"))
    shutil.copy2(LIVE_USER, LIVE_USER.with_name(LIVE_USER.name + f".bak.public-auto-auth-r4.{stamp}"))

    atomic_install(CAND_SERVER, LIVE_SERVER, 0o644)
    atomic_install(CAND_USER, LIVE_USER, 0o644)
    atomic_install(CAND_COLLECTOR, LIVE_COLLECTOR, 0o755)

    ensure_env_lines(ENV_PATH, {
        "HK_PUBLIC_COLLECTOR_TOKEN_FILE": str(TOKEN_PATH),
        "HK_PUBLIC_COLLECTOR_AUTH_BOOTSTRAP": str(BOOTSTRAP_PATH),
        "HK_PUBLIC_COLLECTOR_IDENTITY_FILE": str(IDENTITY_PATH),
        "HK_PUBLIC_COLLECTOR_AUTH_REFRESH_STATUS": str(REFRESH_STATUS_PATH),
    })
    seed_token_file()
    os.chmod(IDENTITY_PATH, 0o600)

    subprocess.check_call(["systemctl", "restart", "hamsterking-license.service"])
    subprocess.check_call(["systemctl", "is-active", "--quiet", "hamsterking-license.service"])
    subprocess.check_call(["systemctl", "is-active", "--quiet", "hamsterking-public-war.timer"])
    subprocess.check_call(["systemctl", "is-active", "--quiet", "hamsterking-public-collector.timer"])

    print("auto_auth_install=PASS")
    print("identity_pin=PASS")
    print("token_seed_present=" + ("yes" if TOKEN_PATH.exists() and TOKEN_PATH.stat().st_size > 0 else "no"))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
