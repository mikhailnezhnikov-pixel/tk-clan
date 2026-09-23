import importlib.util,json,subprocess
from pathlib import Path

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)

dropin=Path("/etc/systemd/system/hamsterking-license.service.d")
matches=[]
if dropin.exists():
    for path in sorted(dropin.glob("*.conf")):
        try:
            lines=path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for line in lines:
            if "HK_MIN_SCRIPT_VERSION" in line:
                matches.append({"file":path.name,"line":line.strip()})

pid_text=subprocess.check_output(
    ["systemctl","show","hamsterking-license.service","-p","MainPID","--value"],
    text=True
).strip()
pid=int(pid_text or "0")
service_min=""
if pid>0:
    raw=Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
    for entry in raw:
        if entry.startswith(b"HK_MIN_SCRIPT_VERSION="):
            service_min=entry.split(b"=",1)[1].decode("utf-8","replace")
            break

print("SERVER_RELEASE_VERSION",server.release_version())
print("INSPECTOR_PROCESS_MIN_SCRIPT_VERSION",server.MIN_SCRIPT_VERSION)
print("MIN_VERSION_DROPINS",json.dumps(matches,ensure_ascii=False))
print("SERVICE_MAIN_PID_OK",pid>0)
print("SERVICE_MIN_SCRIPT_VERSION",service_min)
print("SERVICE_MIN_MATCHES_LATEST",service_min==server.release_version())
