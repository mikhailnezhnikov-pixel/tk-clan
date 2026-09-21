#!/usr/bin/env python3
import base64
import json
import os
import subprocess
import time

TOKEN_PATH="/var/lib/hamsterking-license/public-collector-token"
AUTH_PATH="/var/lib/hamsterking-license/public-collector-auth.json"
IDENTITY_PATH="/var/lib/hamsterking-license/public-collector-identity.sha256"
REFRESH_PATH="/var/lib/hamsterking-license/public-collector-auth-refresh.json"
PROBE_PATH="/var/lib/hamsterking-license/public-collector-auth-probe.json"

def present(path):
    try:
        return os.path.getsize(path)>0
    except OSError:
        return False

print("identity_present="+("yes" if present(IDENTITY_PATH) else "no"))
print("token_present="+("yes" if present(TOKEN_PATH) else "no"))
if present(TOKEN_PATH):
    token=open(TOKEN_PATH,encoding="utf-8").read().strip()
    exp=0
    try:
        part=token.split(".")[1]
        part += "="*(-len(part)%4)
        claims=json.loads(base64.urlsafe_b64decode(part.encode()).decode())
        exp=int(claims.get("exp") or 0)
    except Exception:
        pass
    print("token_exp="+str(exp))
    print("token_seconds_left="+str(exp-int(time.time()) if exp else 0))

print("bootstrap_present="+("yes" if present(AUTH_PATH) else "no"))
if present(AUTH_PATH):
    try:
        doc=json.load(open(AUTH_PATH,encoding="utf-8"))
    except Exception:
        doc={}
    print("bootstrap_auth_type="+str(doc.get("auth_type","")))
    print("bootstrap_platform="+str(doc.get("platform","")))
    print("bootstrap_updated_at="+str(doc.get("updated_at",0)))

print("refresh_backoff_present="+("yes" if os.path.exists(REFRESH_PATH) else "no"))

print("auth_probe_present="+("yes" if present(PROBE_PATH) else "no"))
if present(PROBE_PATH):
    try:
        probe=json.load(open(PROBE_PATH,encoding="utf-8"))
    except Exception:
        probe={}
    print("auth_probe_updated_at="+str(probe.get("updated_at",0)))
    print("auth_probe_local_storage_keys="+json.dumps(probe.get("local_storage_keys",[]),ensure_ascii=False))
    print("auth_probe_session_storage_keys="+json.dumps(probe.get("session_storage_keys",[]),ensure_ascii=False))
    print("auth_probe_cookie_names="+json.dumps(probe.get("cookie_names",[]),ensure_ascii=False))
    print("auth_probe_indexed_db_names="+json.dumps(probe.get("indexed_db_names",[]),ensure_ascii=False))
    print("auth_probe_json_shapes="+json.dumps(probe.get("json_shapes",{}),ensure_ascii=False,sort_keys=True))
    print("auth_probe_telegram_webapp_present="+("yes" if probe.get("telegram_webapp_present") else "no"))
    print("auth_probe_telegram_init_data_present="+("yes" if probe.get("telegram_init_data_present") else "no"))
    print("auth_probe_observed_auth_create="+("yes" if probe.get("observed_auth_create") else "no"))
    print("auth_probe_current_bearer_present="+("yes" if probe.get("current_bearer_present") else "no"))

# Safe static check of the live userscript auth behavior.
try:
    live_path="/opt/hamsterking-license/HamsterKingMobile.user.js"
    src=open(live_path,encoding="utf-8").read()
    version=""
    for line in src.splitlines()[:30]:
        if line.startswith("// @version"):
            version=line.split()[-1]
            break
    print("live_userscript_version="+version)
    print("auth_passive_marker="+("yes" if "AUTH_PASSIVE_SAFETY_R1" in src else "no"))
    print("native_auth_observer_marker="+("yes" if "PUBLIC_COLLECTOR_NATIVE_AUTH_OBSERVER_R1" in src else "no"))
    print("createFresh_call_count="+str(src.count("createFreshGameAuthorization(")))
    ensure_i=src.find("async function ensureGameAuthorization")
    ensure_block=src[ensure_i:ensure_i+1800] if ensure_i>=0 else ""
    print("ensure_calls_createFresh="+("yes" if "createFreshGameAuthorization(" in ensure_block else "no"))
    start_i=src.find("function startAfterNativeGameLogin()")
    start_block=src[start_i:start_i+2600] if start_i>=0 else ""
    print("startup_calls_bootstrapLate="+("yes" if "bootstrapLateGameConnection()" in start_block else "no"))
except Exception:
    print("live_userscript_static_check=unavailable")

# Safe check: does the pinned technical identity correspond to a licensed
# player that has checked in recently? Never print the player ID.
try:
    import hashlib, sqlite3
    expected=open(IDENTITY_PATH,encoding="ascii").read().strip() if present(IDENTITY_PATH) else ""
    db=sqlite3.connect("/var/lib/hamsterking-license/licenses.db")
    db.row_factory=sqlite3.Row
    matched=None
    for row in db.execute("SELECT player_id,active,expires_at FROM licenses"):
        digest=hashlib.sha256(str(row["player_id"]).encode()).hexdigest()
        if expected and digest==expected:
            matched=row
            break
    print("technical_license_present="+("yes" if matched else "no"))
    if matched:
        print("technical_license_active="+("yes" if int(matched["active"] or 0)==1 else "no"))
        device=db.execute(
            "SELECT device_id,last_seen,script_version FROM devices WHERE player_id=? ORDER BY last_seen DESC LIMIT 1",
            (matched["player_id"],)
        ).fetchone()
        print("technical_last_seen="+str(int(device["last_seen"] or 0) if device else 0))
        print("technical_script_version="+str(device["script_version"] if device else ""))
        try:
            import importlib.util
            spec=importlib.util.spec_from_file_location("hk_license_runtime","/opt/hamsterking-license/server.py")
            mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
            allowed=bool(mod.public_collector_auth_sync_allowed(str(matched["player_id"])))
            print("technical_auth_sync_allowed="+("yes" if allowed else "no"))
            try:
                device_id=str(device["device_id"] if device else "")
                status,response=mod.license_check(str(matched["player_id"]), device_id, str(device["script_version"] if device else "1.17.11"), "")
                print("technical_license_check_status="+str(status))
                print("technical_license_check_allowed="+("yes" if bool(response.get("allowed")) else "no"))
                print("technical_license_check_auth_sync="+("yes" if bool(response.get("public_collector_auth_sync")) else "no"))
                print("technical_license_check_token_present="+("yes" if bool(str(response.get("token") or "").strip()) else "no"))
                # Verify the response from the actually running HTTP service, not
                # only the freshly imported server.py source. Never print identity,
                # device ID, token, response body, or auth data.
                try:
                    import urllib.request, urllib.error
                    payload=json.dumps({
                        "player_id":str(matched["player_id"]),
                        "device_id":device_id,
                        "script_version":str(device["script_version"] if device else "1.17.12"),
                    },separators=(",",":")).encode("utf-8")
                    req=urllib.request.Request(
                        "https://hk-license.89.125.1.71.sslip.io/api/v1/check",
                        data=payload,
                        headers={
                            "Content-Type":"application/json",
                            "Origin":"https://app.hamsterking.games",
                            "User-Agent":"TopKing-Safe-Runtime-Check/1",
                        },
                        method="POST",
                    )
                    with urllib.request.urlopen(req,timeout=15) as http_response:
                        live_status=int(http_response.status)
                        live_body=json.loads(http_response.read(200000).decode("utf-8"))
                    print("technical_live_http_check_status="+str(live_status))
                    print("technical_live_http_check_allowed="+("yes" if bool(live_body.get("allowed")) else "no"))
                    print("technical_live_http_check_auth_sync="+("yes" if bool(live_body.get("public_collector_auth_sync")) else "no"))
                    print("technical_live_http_check_token_present="+("yes" if bool(str(live_body.get("token") or "").strip()) else "no"))
                except Exception:
                    print("technical_live_http_check_status=unavailable")
            except Exception:
                print("technical_license_check_allowed=unavailable")
        except Exception:
            print("technical_auth_sync_allowed=unavailable")
    db.close()
except Exception as exc:
    print("technical_license_check=unavailable")

# Safe reverse-proxy check: only report whether auth-sync was requested and
# the latest HTTP status/time; never print IP, token, query/body, or User-Agent.
sync_events=[]
for log_path in ("/var/log/nginx/access.log", "/var/log/nginx/access.log.1"):
    try:
        lines=open(log_path,encoding="utf-8",errors="replace").read().splitlines()[-5000:]
    except OSError:
        continue
    for line in lines:
        if "/api/v1/public-collector/auth-sync" not in line:
            continue
        import re
        tm=re.search(r"\[([^\]]+)\]", line)
        st=re.search(r'"\s+(\d{3})\s+', line)
        sync_events.append((tm.group(1) if tm else "", st.group(1) if st else ""))
print("auth_sync_request_seen="+("yes" if sync_events else "no"))
probe_events=[]
for log_path in ("/var/log/nginx/access.log", "/var/log/nginx/access.log.1"):
    try:
        lines=open(log_path,encoding="utf-8",errors="replace").read().splitlines()[-5000:]
    except OSError:
        continue
    for line in lines:
        if "/api/v1/public-collector/auth-probe" not in line:
            continue
        import re
        tm=re.search(r"\[([^\]]+)\]", line)
        st=re.search(r'"\s+(\d{3})\s+', line)
        probe_events.append((tm.group(1) if tm else "", st.group(1) if st else ""))
print("auth_probe_request_seen="+("yes" if probe_events else "no"))
if probe_events:
    print("auth_probe_latest_time="+probe_events[-1][0])
    print("auth_probe_latest_status="+probe_events[-1][1])
try:
    server_src=open("/opt/hamsterking-license/server.py",encoding="utf-8").read()
    print("auth_probe_server_marker="+("yes" if "PUBLIC_COLLECTOR_AUTH_PROBE_R1" in server_src else "no"))
    print("auth_probe_server_route="+("yes" if "/api/v1/public-collector/auth-probe" in server_src else "no"))
except Exception:
    print("auth_probe_server_marker=unavailable")
if sync_events:
    print("auth_sync_latest_time="+sync_events[-1][0])
    print("auth_sync_latest_status="+sync_events[-1][1])

# Safe server release-gate inspection.
try:
    server_src=open("/opt/hamsterking-license/server.py",encoding="utf-8").read()
    min_line=next((line.strip() for line in server_src.splitlines() if line.startswith("MIN_SCRIPT_VERSION =")), "")
    print("server_min_version_line="+min_line)
    li=server_src.find("def license_check(")
    block=server_src[li:li+7000] if li>=0 else ""
    print("license_check_present="+("yes" if li>=0 else "no"))
    print("license_check_uses_min_version="+("yes" if "MIN_SCRIPT_VERSION" in block else "no"))
    print("license_check_returns_update_required="+("yes" if "update_required" in block else "no"))
    print("license_check_returns_auth_sync_flag="+("yes" if "public_collector_auth_sync" in block else "no"))
except Exception:
    print("server_release_gate_check=unavailable")

# Safe runtime wiring check: confirm which process systemd runs and which
# local upstream nginx targets. Never print environment variables or request data.
try:
    show=subprocess.check_output(
        ["systemctl","show","hamsterking-license.service","--property=MainPID","--property=ExecStart","--no-pager"],
        text=True,stderr=subprocess.STDOUT,timeout=10,
    )
    main_pid=""
    for line in show.splitlines():
        if line.startswith("MainPID="):
            main_pid=line.split("=",1)[1].strip()
    print("license_service_main_pid_present="+("yes" if main_pid and main_pid!="0" else "no"))
    print("license_service_execstart_live_server="+("yes" if "/opt/hamsterking-license/server.py" in show else "no"))
    if main_pid and main_pid!="0":
        try:
            cmd=open(f"/proc/{int(main_pid)}/cmdline","rb").read(8192).replace(b"\\x00",b" ").decode("utf-8","replace")
        except Exception:
            cmd=""
        print("license_service_cmdline_live_server="+("yes" if "/opt/hamsterking-license/server.py" in cmd else "no"))
except Exception:
    print("license_service_wiring=unavailable")

try:
    nginx_text=subprocess.check_output(["nginx","-T"],text=True,stderr=subprocess.STDOUT,timeout=10)
    import re
    proxy_targets=[]
    for target in re.findall(r"\\bproxy_pass\\s+(https?://[^;\\s]+)",nginx_text):
        if target not in proxy_targets:
            proxy_targets.append(target)
    print("nginx_proxy_targets="+json.dumps(proxy_targets,ensure_ascii=False))
    print("nginx_config_mentions_license_host="+("yes" if "hk-license.89.125.1.71.sslip.io" in nginx_text else "no"))
except Exception:
    print("nginx_runtime_wiring=unavailable")

# Inspect only non-secret runtime routing/path settings.
try:
    identity_env=""
    if main_pid and main_pid!="0":
        raw=open(f"/proc/{int(main_pid)}/environ","rb").read(2_000_000)
        for item in raw.split(b"\\x00"):
            if item.startswith(b"HK_PUBLIC_COLLECTOR_IDENTITY_FILE="):
                identity_env=item.split(b"=",1)[1].decode("utf-8","replace")
                break
    print("license_service_identity_env_present="+("yes" if identity_env else "no"))
    print("license_service_identity_env_default="+("yes" if (not identity_env or identity_env==IDENTITY_PATH) else "no"))
except Exception:
    print("license_service_identity_env_check=unavailable")

try:
    nginx_files=[]
    for base in ("/etc/nginx/nginx.conf","/etc/nginx/sites-enabled","/etc/nginx/conf.d"):
        if os.path.isfile(base):
            nginx_files.append(base)
        elif os.path.isdir(base):
            for name in sorted(os.listdir(base)):
                path=os.path.join(base,name)
                if os.path.isfile(path):
                    nginx_files.append(path)
    proxy_targets=[]
    license_config_files=0
    for path in nginx_files:
        try:
            text_value=open(path,encoding="utf-8",errors="replace").read()
        except OSError:
            continue
        if "hk-license.89.125.1.71.sslip.io" in text_value:
            license_config_files += 1
        import re
        for target in re.findall(r"\\bproxy_pass\\s+(https?://[^;\\s]+)",text_value):
            if target not in proxy_targets:
                proxy_targets.append(target)
    print("nginx_file_proxy_targets="+json.dumps(proxy_targets,ensure_ascii=False))
    print("nginx_license_config_files="+str(license_config_files))
except Exception:
    print("nginx_file_wiring=unavailable")

try:
    out=subprocess.check_output(["ss","-ltnp"],text=True,stderr=subprocess.STDOUT,timeout=10)
    pid_marker=f"pid={main_pid}," if main_pid and main_pid!="0" else ""
    service_lines=[line.strip() for line in out.splitlines() if pid_marker and pid_marker in line]
    # Only expose local listen addresses/ports for the license service.
    print("license_service_listeners="+json.dumps(service_lines,ensure_ascii=False))
except Exception:
    print("license_service_listeners=unavailable")

for unit,label in (
    ("hamsterking-public-war.service","war_journal"),
    ("hamsterking-public-collector.service","ratings_journal"),
):
    print("=== "+label+" ===")
    try:
        out=subprocess.check_output(
            ["journalctl","-u",unit,"-n","12","--no-pager"],
            text=True,stderr=subprocess.STDOUT,timeout=10,
        )
    except Exception:
        out=""
    for line in out.splitlines():
        if "[public-collector]" in line or "Starting " in line or "Finished " in line:
            print(line)
