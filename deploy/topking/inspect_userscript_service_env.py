import json, os, shlex, subprocess
from pathlib import Path

service="hamsterking-license.service"

def run(*args):
    return subprocess.check_output(list(args), text=True, stderr=subprocess.STDOUT).strip()

def safe_read(path):
    try:
        text=Path(path).read_text(encoding="utf-8",errors="replace")
    except Exception as exc:
        return {"path":path,"error":type(exc).__name__}
    lines=[]
    for line in text.splitlines():
        if "HK_MIN_SCRIPT_VERSION" in line or "EnvironmentFile" in line or "Environment=" in line:
            lines.append(line.strip())
    return {"path":path,"lines":lines}

unit_env=run("systemctl","show",service,"-p","Environment","--value")
env_files_raw=run("systemctl","show",service,"-p","EnvironmentFiles","--value")
dropins=run("systemctl","show",service,"-p","DropInPaths","--value")
main_pid=int(run("systemctl","show",service,"-p","MainPID","--value") or "0")

unit_min=[]
try:
    unit_min=[token.split("=",1)[1] for token in shlex.split(unit_env)
              if token.startswith("HK_MIN_SCRIPT_VERSION=")]
except Exception:
    pass

proc_min=[]
if main_pid>0:
    for entry in Path(f"/proc/{main_pid}/environ").read_bytes().split(b"\0"):
        if entry.startswith(b"HK_MIN_SCRIPT_VERSION="):
            proc_min.append(entry.split(b"=",1)[1].decode("utf-8","replace"))

paths=set()
for token in shlex.split(env_files_raw):
    value=token
    if value.startswith("-"):
        value=value[1:]
    if value and value.startswith("/"):
        paths.add(value)
for value in dropins.split():
    if value.startswith("/"):
        paths.add(value)
for value in [
    "/etc/environment",
    "/etc/default/hamsterking-license",
    "/etc/sysconfig/hamsterking-license",
    "/etc/systemd/system/hamsterking-license.service",
]:
    if Path(value).exists():
        paths.add(value)

print("SERVICE",service)
print("MAIN_PID",main_pid)
print("UNIT_MIN_VALUES",json.dumps(unit_min,ensure_ascii=False))
print("PROCESS_MIN_VALUES",json.dumps(proc_min,ensure_ascii=False))
print("ENVIRONMENT_FILES_RAW",env_files_raw)
print("DROPIN_PATHS",dropins)
for path in sorted(paths):
    print("SOURCE",json.dumps(safe_read(path),ensure_ascii=False))
