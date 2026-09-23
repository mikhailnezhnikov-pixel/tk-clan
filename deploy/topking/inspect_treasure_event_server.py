import json,subprocess,shlex
from pathlib import Path

service="hamsterking-license.service"
cat=subprocess.check_output(["systemctl","cat",service],text=True,stderr=subprocess.STDOUT)
unit_lines=[]
current_source=""
for line in cat.splitlines():
    if line.startswith("# "):
        current_source=line[2:].strip()
    if "HK_MIN_SCRIPT_VERSION" in line:
        unit_lines.append({"source":current_source,"line":line.strip()})

env_value=subprocess.check_output(
    ["systemctl","show",service,"-p","Environment","--value"],text=True
).strip()
show_min=[]
try:
    for token in shlex.split(env_value):
        if token.startswith("HK_MIN_SCRIPT_VERSION="):
            show_min.append(token.split("=",1)[1])
except Exception:
    pass

dropins=subprocess.check_output(
    ["systemctl","show",service,"-p","DropInPaths","--value"],text=True
).strip()
execstart=subprocess.check_output(
    ["systemctl","show",service,"-p","ExecStart","--value"],text=True
).strip()

main_pid=int(subprocess.check_output(
    ["systemctl","show",service,"-p","MainPID","--value"],text=True
).strip() or "0")
proc_min=""
if main_pid>0:
    raw=Path(f"/proc/{main_pid}/environ").read_bytes().split(b"\0")
    for entry in raw:
        if entry.startswith(b"HK_MIN_SCRIPT_VERSION="):
            proc_min=entry.split(b"=",1)[1].decode("utf-8","replace")
            break

print("UNIT_MIN_LINES",json.dumps(unit_lines,ensure_ascii=False))
print("SYSTEMD_SHOW_MIN_VALUES",json.dumps(show_min,ensure_ascii=False))
print("DROPIN_PATHS",dropins)
print("EXECSTART",execstart[:2000])
print("PROCESS_MIN_VALUE",proc_min)
