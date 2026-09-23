import json,subprocess,shlex
from pathlib import Path

service="hamsterking-license.service"

unit_env=subprocess.check_output(
    ["systemctl","show",service,"-p","Environment","--value"],text=True
).strip()
unit_min=[]
try:
    unit_min=[token.split("=",1)[1] for token in shlex.split(unit_env)
              if token.startswith("HK_MIN_SCRIPT_VERSION=")]
except Exception:
    pass

env_files=subprocess.check_output(
    ["systemctl","show",service,"-p","EnvironmentFiles","--value"],text=True
).strip()

manager_text=subprocess.check_output(["systemctl","show-environment"],text=True)
manager_min=[]
for line in manager_text.splitlines():
    if line.startswith("HK_MIN_SCRIPT_VERSION="):
        manager_min.append(line.split("=",1)[1])

pid=int(subprocess.check_output(
    ["systemctl","show",service,"-p","MainPID","--value"],text=True
).strip() or "0")
proc_min=[]
if pid>0:
    for entry in Path(f"/proc/{pid}/environ").read_bytes().split(b"\0"):
        if entry.startswith(b"HK_MIN_SCRIPT_VERSION="):
            proc_min.append(entry.split(b"=",1)[1].decode("utf-8","replace"))

print("UNIT_MIN_VALUES",json.dumps(unit_min,ensure_ascii=False))
print("ENVIRONMENT_FILES",env_files)
print("MANAGER_MIN_VALUES",json.dumps(manager_min,ensure_ascii=False))
print("PROCESS_MIN_VALUES",json.dumps(proc_min,ensure_ascii=False))
print("PROCESS_MIN_ENTRY_COUNT",len(proc_min))
