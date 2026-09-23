import importlib.util,json
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

print("SERVER_RELEASE_VERSION",server.release_version())
print("SERVER_MIN_SCRIPT_VERSION",server.MIN_SCRIPT_VERSION)
print("MIN_VERSION_DROPINS",json.dumps(matches,ensure_ascii=False))
