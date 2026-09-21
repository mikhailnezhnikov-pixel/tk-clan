#!/usr/bin/env python3
import os
import json
import sqlite3
import time
import urllib.error
import urllib.request

DB="/var/lib/hamsterking-license/licenses.db"
PUBLIC="https://hk-license.89.125.1.71.sslip.io"
SITE="https://tk-clan.ru"
KINDS=("influence","power","clans","alliance_power","alliance_influence","alliance_defense")

def yes(v):
    return "yes" if bool(v) else "no"

SENSITIVE_PUBLIC_KEYS={"token","game_token","auth_data","authorization","device_id","source_player_id","license_token"}

def sensitive_keys(value):
    found=set()
    if isinstance(value,dict):
        for key,child in value.items():
            name=str(key or "").strip().lower()
            if name in SENSITIVE_PUBLIC_KEYS:
                found.add(name)
            found.update(sensitive_keys(child))
    elif isinstance(value,list):
        for child in value:
            found.update(sensitive_keys(child))
    return found

def get_json(url):
    req=urllib.request.Request(
        url,
        headers={
            "Accept":"application/json",
            "Origin":SITE,
            "User-Agent":"TopKing-Public-E2E-Check/1",
        },
        method="GET",
    )
    with urllib.request.urlopen(req,timeout=25) as response:
        body=json.loads(response.read(2_000_000).decode("utf-8"))
        return int(response.status),body,response.headers.get("Access-Control-Allow-Origin","")

def get_text(url):
    req=urllib.request.Request(
        url,
        headers={"Accept":"text/html","User-Agent":"TopKing-Public-E2E-Check/1"},
        method="GET",
    )
    with urllib.request.urlopen(req,timeout=25) as response:
        return int(response.status),response.read(2_000_000).decode("utf-8","replace")

now=int(time.time())
db=sqlite3.connect(DB)
db.row_factory=sqlite3.Row

war_row=db.execute(
    "SELECT snapshot_json,updated_at FROM public_clan_war_snapshot WHERE singleton=1"
).fetchone()
db_war_updated=int(war_row["updated_at"] or 0) if war_row else 0
db_war_active=False
if war_row:
    try:
        db_war_active=bool(json.loads(war_row["snapshot_json"] or "{}"))
    except Exception:
        pass

print("e2e_revision=PUBLIC_OUTPUT_E2E_R2")
print("db_war_present="+yes(war_row))
print("db_war_active="+yes(db_war_active))
print("db_war_age_seconds="+str(max(0,now-db_war_updated) if db_war_updated else 0))

war_status,war_doc,war_cors=get_json(PUBLIC+"/api/v1/public/clan-war")
api_war_updated=int(war_doc.get("updated_at") or 0) if isinstance(war_doc,dict) else 0
print("api_war_status="+str(war_status))
print("api_war_ok="+yes(isinstance(war_doc,dict) and war_doc.get("ok")))
print("api_war_active="+yes(isinstance(war_doc,dict) and war_doc.get("active")))
print("api_war_stale="+yes(isinstance(war_doc,dict) and war_doc.get("stale")))
print("api_war_cors_site="+yes(war_cors==SITE))
api_war_active=bool(isinstance(war_doc,dict) and war_doc.get("active"))
war_db_state_ok=(
    (api_war_active and bool(war_row) and db_war_active and api_war_updated==db_war_updated and api_war_updated>0)
    or ((not api_war_active) and (not war_row) and api_war_updated==0)
)
print("api_war_matches_db_state="+yes(war_db_state_ok))
print("api_war_age_seconds="+str(max(0,now-api_war_updated) if api_war_updated else 0))
war_payload=war_doc.get("war") if isinstance(war_doc,dict) and isinstance(war_doc.get("war"),dict) else {}
war_opponent_ok=bool(str(war_payload.get("opponent") or "").strip())
try:
    war_hp=float(war_payload.get("opponent_hp"))
    war_hp_max=float(war_payload.get("opponent_hp_max"))
    war_hp_ok=(war_hp>=0 and war_hp_max>0 and war_hp<=war_hp_max)
except Exception:
    war_hp_ok=False
war_payload_shape_ok=(war_opponent_ok and war_hp_ok) if api_war_active else (not war_payload)
print("api_war_opponent_present="+yes(war_opponent_ok))
print("api_war_hp_shape_ok="+yes(war_hp_ok))
war_sensitive=sensitive_keys(war_doc)
print("api_war_payload_shape_ok="+yes(war_payload_shape_ok))
print("api_war_sensitive_keys_absent="+yes(not war_sensitive))

ratings_all_ok=True
for kind in KINDS:
    row=db.execute(
        "SELECT COUNT(*) AS n,MAX(updated_at) AS updated_at FROM public_rating_snapshots WHERE kind=?",
        (kind,),
    ).fetchone()
    db_count=int(row["n"] or 0)
    db_updated=int(row["updated_at"] or 0)
    status,doc,cors=get_json(PUBLIC+"/api/v1/public/ratings?kind="+kind)
    rows=doc.get("rows") if isinstance(doc,dict) and isinstance(doc.get("rows"),list) else []
    api_updated=int(doc.get("updated_at") or 0) if isinstance(doc,dict) else 0
    ranks=[]
    for item in rows:
        try:
            ranks.append(int(item.get("rank")))
        except Exception:
            pass
    sorted_unique=(ranks==sorted(ranks) and len(ranks)==len(set(ranks)))
    row_shape_ok=True
    for item in rows:
        if not isinstance(item,dict):
            row_shape_ok=False
            break
        try:
            rank_value=int(item.get("rank"))
            value_number=float(item.get("value"))
        except Exception:
            row_shape_ok=False
            break
        if rank_value<1 or not str(item.get("name") or "").strip() or value_number<0:
            row_shape_ok=False
            break
    sensitive=sensitive_keys(doc)
    kind_ok=(
        status==200
        and bool(doc.get("ok"))
        and db_count>0
        and len(rows)==db_count
        and api_updated==db_updated
        and api_updated>0
        and sorted_unique
        and row_shape_ok
        and not sensitive
        and cors==SITE
    )
    ratings_all_ok=ratings_all_ok and kind_ok
    print("rating_"+kind+"_status="+str(status))
    print("rating_"+kind+"_db_count="+str(db_count))
    print("rating_"+kind+"_api_count="+str(len(rows)))
    print("rating_"+kind+"_matches_db="+yes(len(rows)==db_count and api_updated==db_updated and db_count>0))
    print("rating_"+kind+"_ranks_sorted_unique="+yes(sorted_unique))
    print("rating_"+kind+"_row_shape_ok="+yes(row_shape_ok))
    print("rating_"+kind+"_sensitive_keys_absent="+yes(not sensitive))
    print("rating_"+kind+"_cors_site="+yes(cors==SITE))
    print("rating_"+kind+"_stale="+yes(doc.get("stale") if isinstance(doc,dict) else True))
    print("rating_"+kind+"_age_seconds="+str(max(0,now-api_updated) if api_updated else 0))

db.close()

wars_status,wars_html=get_text(SITE+"/wars/")
ratings_status,ratings_html=get_text(SITE+"/ratings/")
print("site_wars_status="+str(wars_status))
print("site_wars_public_api_marker="+yes("/api/v1/public/clan-war" in wars_html))
print("site_wars_refresh_marker="+yes("setInterval(load,60000)" in wars_html.replace(" ","")))
print("site_ratings_status="+str(ratings_status))
print("site_ratings_public_api_marker="+yes("/api/v1/public/ratings?kind=" in ratings_html))
print("site_ratings_alliance_controls="+yes("alliance_power" in ratings_html and "alliance_influence" in ratings_html and "alliance_defense" in ratings_html))
print("site_ratings_refresh_marker="+yes("setInterval(load,300000)" in ratings_html.replace(" ","")))

# Operational schedule checks. Only unit state and schedule expressions are
# exposed; no environment or credentials are read.
import subprocess
def unit_text(name):
    return subprocess.check_output(
        ["systemctl","cat",name,"--no-pager"],
        text=True,stderr=subprocess.STDOUT,timeout=10,
    )
def unit_state(name,verb):
    result=subprocess.run(
        ["systemctl",verb,name],
        stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=10,
    )
    return result.returncode==0
def unit_show(name):
    return subprocess.check_output(
        ["systemctl","show",name,"--property=LastTriggerUSec","--property=NextElapseUSecRealtime","--no-pager"],
        text=True,stderr=subprocess.STDOUT,timeout=10,
    )

war_timer=unit_text("hamsterking-public-war.timer")
ratings_timer=unit_text("hamsterking-public-collector.timer")
war_timer_schedule=("OnCalendar=*-*-* *:03/10:00" in war_timer and "RandomizedDelaySec=30" in war_timer)
ratings_timer_schedule=("OnCalendar=*-*-* 16:00:00 Europe/Moscow" in ratings_timer and "RandomizedDelaySec=0" in ratings_timer)
war_timer_active=unit_state("hamsterking-public-war.timer","is-active")
war_timer_enabled=unit_state("hamsterking-public-war.timer","is-enabled")
ratings_timer_active=unit_state("hamsterking-public-collector.timer","is-active")
ratings_timer_enabled=unit_state("hamsterking-public-collector.timer","is-enabled")
war_timer_show=unit_show("hamsterking-public-war.timer")
ratings_timer_show=unit_show("hamsterking-public-collector.timer")
war_timer_next=bool([line for line in war_timer_show.splitlines() if line.startswith("NextElapseUSecRealtime=") and line.split("=",1)[1].strip()])
ratings_timer_next=bool([line for line in ratings_timer_show.splitlines() if line.startswith("NextElapseUSecRealtime=") and line.split("=",1)[1].strip()])
print("war_timer_active="+yes(war_timer_active))
print("war_timer_enabled="+yes(war_timer_enabled))
print("war_timer_schedule_10m="+yes(war_timer_schedule))
print("war_timer_next_present="+yes(war_timer_next))
print("ratings_timer_active="+yes(ratings_timer_active))
print("ratings_timer_enabled="+yes(ratings_timer_enabled))
print("ratings_timer_schedule_daily="+yes(ratings_timer_schedule))
print("ratings_timer_next_present="+yes(ratings_timer_next))

# Security regression guards for the collector auth bridge. These are static
# checks against the live server/userscript and do not touch player state.
server_src=open("/opt/hamsterking-license/server.py",encoding="utf-8").read()
probe_route_absent=all(marker not in server_src for marker in (
    "/api/v1/public-collector/auth-probe",
    "accept_public_collector_auth_probe",
    "PUBLIC_COLLECTOR_AUTH_PROBE",
))
sync_route_i=server_src.find('path == "/api/v1/public-collector/auth-sync"')
sync_route_block=server_src[sync_route_i:sync_route_i+2600] if sync_route_i>=0 else ""
sync_guard=sync_route_block.find("public_collector_auth_sync_allowed(player_id)")
sync_read=sync_route_block.find("self.read_json(")
server_sync_guard_ok=(sync_route_i>=0 and sync_guard>=0 and sync_read>=0 and sync_guard<sync_read)
server_guard_ok=(probe_route_absent and server_sync_guard_ok)
print("server_auth_probe_absent="+yes(probe_route_absent))
print("server_sync_identity_guard_before_body="+yes(server_sync_guard_ok))

userscript_src=open("/opt/hamsterking-license/HamsterKingMobile.user.js",encoding="utf-8").read()
client_probe_absent=all(marker not in userscript_src for marker in (
    "PUBLIC_COLLECTOR_AUTH_PROBE_URL",
    "sendPublicCollectorAuthProbe",
    "buildPublicCollectorAuthProbe",
    "safeStorageProbeArea",
    "/api/v1/public-collector/auth-probe",
))
sync_i=userscript_src.find("async function maybeSyncPublicCollectorAuthorization")
sync_block=userscript_src[sync_i:sync_i+2200] if sync_i>=0 else ""
client_sync_guard=("!licenseState.publicCollectorAuthSync" in sync_block)
client_xhr=("AUTH_BRIDGE_XHR_TRANSPORT_R1" in userscript_src and "function publicCollectorServerPost" in userscript_src)
client_passive=("AUTH_PASSIVE_SAFETY_R1" in userscript_src and "auth-create-blocked-passive-only" in userscript_src)
start_i=userscript_src.find("function startAfterNativeGameLogin()")
start_block=userscript_src[start_i:start_i+3200] if start_i>=0 else ""
ensure_i=userscript_src.find("async function ensureGameAuthorization")
ensure_block=userscript_src[ensure_i:ensure_i+2400] if ensure_i>=0 else ""
prelogin_marker=("PRELOGIN_ZERO_GAME_API_R1" in userscript_src)
startup_no_bootstrap_player_me=(
    start_i>=0
    and "bootstrapLateGameConnection()" not in start_block
    and "apiJson('/player/me'" not in start_block
    and 'apiJson("/player/me"' not in start_block
)
ensure_never_creates_auth=(ensure_i>=0 and "createFreshGameAuthorization(" not in ensure_block)
explore_canon_ok=("HK_EXPLORE_CANON_REV='explore-e3-single-20260920-r9-runner'" in userscript_src)
map_concurrency_ok=("const HK_MAP_READ_CONCURRENCY = 5;" in userscript_src)
public_snapshot_canon_ok=("HK_PUBLIC_SNAPSHOT_CLIENT_REV = 'public-server-only-20260920-r2'" in userscript_src)

print("client_auth_probe_absent="+yes(client_probe_absent))
print("client_sync_technical_guard="+yes(client_sync_guard))
print("client_auth_bridge_xhr="+yes(client_xhr))
print("client_auth_create_passive="+yes(client_passive))
print("client_prelogin_zero_game_api_marker="+yes(prelogin_marker))
print("client_startup_no_bootstrap_player_me="+yes(startup_no_bootstrap_player_me))
print("client_ensure_never_creates_auth="+yes(ensure_never_creates_auth))
print("protected_explore_canon="+yes(explore_canon_ok))
print("protected_map_concurrency_5="+yes(map_concurrency_ok))
print("protected_public_snapshot_canon="+yes(public_snapshot_canon_ok))
collector_isolation_static_ok=(server_guard_ok and client_probe_absent and client_sync_guard and client_xhr and client_passive)
userscript_safety_invariants_ok=all((
    prelogin_marker,
    startup_no_bootstrap_player_me,
    ensure_never_creates_auth,
    explore_canon_ok,
    map_concurrency_ok,
    public_snapshot_canon_ok,
))

# Live credential filesystem permissions. The token may be last written either
# by the root collector or by the unprivileged license service; both owners are
# valid, but all credential files must remain private.
import stat
service_show=subprocess.check_output(
    ["systemctl","show","hamsterking-license.service","--property=MainPID","--no-pager"],
    text=True,stderr=subprocess.STDOUT,timeout=10,
)
service_pid=next((line.split("=",1)[1].strip() for line in service_show.splitlines() if line.startswith("MainPID=")),"")
service_uid=-1
if service_pid and service_pid!="0":
    status_text=open(f"/proc/{int(service_pid)}/status",encoding="utf-8",errors="replace").read()
    uid_line=next((line for line in status_text.splitlines() if line.startswith("Uid:")),"")
    service_uid=int(uid_line.split()[1]) if uid_line else -1

data_dir="/var/lib/hamsterking-license"
identity_path=data_dir+"/public-collector-identity.sha256"
token_path=data_dir+"/public-collector-token"
bootstrap_path=data_dir+"/public-collector-auth.json"
probe_path=data_dir+"/public-collector-auth-probe.json"
refresh_path=data_dir+"/public-collector-auth-refresh.json"
env_path="/etc/hamsterking-public-collector.env"

def mode_owner_ok(path,mode,owners):
    try:
        st=os.stat(path)
        return stat.S_IMODE(st.st_mode)==mode and st.st_uid in owners
    except OSError:
        return False

dir_ok=False
try:
    st=os.stat(data_dir)
    dir_ok=(service_uid>=0 and st.st_uid==service_uid and stat.S_IMODE(st.st_mode)==0o750)
except OSError:
    pass
identity_perm_ok=(service_uid>=0 and mode_owner_ok(identity_path,0o600,{service_uid}))
bootstrap_perm_ok=(service_uid>=0 and mode_owner_ok(bootstrap_path,0o600,{service_uid}))
probe_absent=(not os.path.exists(probe_path))
token_perm_ok=(service_uid>=0 and mode_owner_ok(token_path,0o600,{0,service_uid}))
env_perm_ok=mode_owner_ok(env_path,0o600,{0})
refresh_perm_ok=True
if os.path.exists(refresh_path):
    refresh_perm_ok=(service_uid>=0 and mode_owner_ok(refresh_path,0o600,{0,service_uid}))

env_keys=set()
try:
    for raw in open(env_path,encoding="utf-8",errors="replace"):
        line=raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        env_keys.add(line.split("=",1)[0].strip())
except OSError:
    pass
legacy_static_token_absent=("HK_PUBLIC_COLLECTOR_GAME_TOKEN" not in env_keys)
token_file_env_present=("HK_PUBLIC_COLLECTOR_TOKEN_FILE" in env_keys)
bootstrap_env_present=("HK_PUBLIC_COLLECTOR_AUTH_BOOTSTRAP" in env_keys)
collector_src=open("/opt/hamsterking-license/public_collector.py",encoding="utf-8").read()
collector_self_heal_live=("PUBLIC_COLLECTOR_BOOTSTRAP_SELF_HEAL_R1" in collector_src and "r5-bootstrap-self-heal" in collector_src)
token_lifecycle_hardening_ok=all((
    legacy_static_token_absent,
    token_file_env_present,
    bootstrap_env_present,
    collector_self_heal_live,
))

print("collector_data_dir_private="+yes(dir_ok))
print("collector_identity_private="+yes(identity_perm_ok))
print("collector_token_private="+yes(token_perm_ok))
print("collector_bootstrap_private="+yes(bootstrap_perm_ok))
print("collector_probe_absent="+yes(probe_absent))
print("collector_env_private="+yes(env_perm_ok))
print("collector_refresh_status_private="+yes(refresh_perm_ok))
print("collector_legacy_static_token_absent="+yes(legacy_static_token_absent))
print("collector_token_file_env_present="+yes(token_file_env_present))
print("collector_bootstrap_env_present="+yes(bootstrap_env_present))
print("collector_self_heal_live="+yes(collector_self_heal_live))
credential_permissions_ok=all((dir_ok,identity_perm_ok,token_perm_ok,bootstrap_perm_ok,probe_absent,env_perm_ok,refresh_perm_ok))

war_ok=(
    war_status==200
    and bool(war_doc.get("ok"))
    and war_db_state_ok
    and war_cors==SITE
    and war_payload_shape_ok
    and not war_sensitive
)
site_ok=(
    wars_status==200
    and ratings_status==200
    and "/api/v1/public/clan-war" in wars_html
    and "/api/v1/public/ratings?kind=" in ratings_html
)
timers_ok=(
    war_timer_active and war_timer_enabled and war_timer_schedule and war_timer_next
    and ratings_timer_active and ratings_timer_enabled and ratings_timer_schedule and ratings_timer_next
)
print("war_e2e="+("PASS" if war_ok else "FAIL"))
print("ratings_e2e="+("PASS" if ratings_all_ok else "FAIL"))
print("site_binding_e2e="+("PASS" if site_ok else "FAIL"))
print("collector_timers_e2e="+("PASS" if timers_ok else "FAIL"))
print("collector_isolation_static="+("PASS" if collector_isolation_static_ok else "FAIL"))
print("userscript_safety_invariants="+("PASS" if userscript_safety_invariants_ok else "FAIL"))
print("collector_credential_permissions="+("PASS" if credential_permissions_ok else "FAIL"))
print("collector_token_lifecycle_hardening="+("PASS" if token_lifecycle_hardening_ok else "FAIL"))

if not (war_ok and ratings_all_ok and site_ok and timers_ok and collector_isolation_static_ok and userscript_safety_invariants_ok and credential_permissions_ok and token_lifecycle_hardening_ok):
    raise SystemExit(2)

print("PUBLIC_OUTPUT_E2E=PASS")
