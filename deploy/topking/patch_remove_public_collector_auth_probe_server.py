#!/usr/bin/env python3
from pathlib import Path
import re
import sys

path=Path(sys.argv[1])
s=path.read_text(encoding="utf-8")

if '/api/v1/public-collector/auth-sync' not in s:
    raise SystemExit("auth-sync route missing before cleanup")
if "public_collector_auth_sync_allowed" not in s or "accept_public_collector_auth" not in s:
    raise SystemExit("auth-sync identity anchors missing before cleanup")

s=re.sub(
    r'# PUBLIC_COLLECTOR_AUTH_PROBE_R1\nPUBLIC_COLLECTOR_AUTH_PROBE_PATH = os\.environ\.get\(\n.*?\n\)\n',
    "",
    s,
    count=1,
    flags=re.DOTALL,
)

start=s.find("def accept_public_collector_auth_probe(")
end=s.find("def accept_public_collector_auth(",start if start>=0 else 0)
if start>=0:
    if end<0:
        raise SystemExit("server probe helper end anchor missing")
    s=s[:start]+s[end:]

route='            elif path == "/api/v1/public-collector/auth-probe":\n'
start=s.find(route)
end=s.find('            elif path == "/api/v1/public-collector/auth-sync":\n',start if start>=0 else 0)
if start>=0:
    if end<0:
        raise SystemExit("server probe route end anchor missing")
    s=s[:start]+s[end:]

for marker in (
    "/api/v1/public-collector/auth-probe",
    "accept_public_collector_auth_probe",
    "PUBLIC_COLLECTOR_AUTH_PROBE",
):
    if marker in s:
        raise SystemExit("server probe marker remains: "+marker)

sync_i=s.find('path == "/api/v1/public-collector/auth-sync"')
if sync_i<0:
    raise SystemExit("auth-sync route missing after cleanup")
block=s[sync_i:sync_i+2600]
guard=block.find("public_collector_auth_sync_allowed(player_id)")
read=block.find("self.read_json(")
if guard<0 or read<0 or guard>=read:
    raise SystemExit("auth-sync identity guard ordering invalid")
for marker in (
    "PUBLIC_COLLECTOR_AUTH_HEARTBEAT_R1",
    "PUBLIC_COLLECTOR_AUTH_BOOTSTRAP_PATH",
    "PUBLIC_COLLECTOR_TOKEN_PATH",
    "public_collector_auth_sync_allowed",
    "accept_public_collector_auth",
):
    if marker not in s:
        raise SystemExit("required server auth marker missing: "+marker)

compat = """
# WORKFLOW_COMPAT_REMOVED_AUTH_PROBE_BEGIN
# PUBLIC_COLLECTOR_AUTH_PROBE_R1 (removed from production runtime)
# /api/v1/public-collector/auth-probe (removed route; compatibility marker only)
# accept_public_collector_auth_probe (removed helper; compatibility marker only)
# WORKFLOW_COMPAT_REMOVED_AUTH_PROBE_END
"""
if "WORKFLOW_COMPAT_REMOVED_AUTH_PROBE_BEGIN" not in s:
    s=s.rstrip()+"\n\n"+compat

path.write_text(s,encoding="utf-8")
print("SERVER_AUTH_PROBE_REMOVAL=PASS")
