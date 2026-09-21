#!/usr/bin/env python3
from pathlib import Path
import re
import sys

path=Path(sys.argv[1])
s=path.read_text(encoding="utf-8")

if "// @version      1.17.12" not in s or "const BUILD_VERSION = '1.17.12';" not in s:
    raise SystemExit("unexpected userscript version")
if "PUBLIC_COLLECTOR_AUTH_SYNC_URL" not in s or "async function maybeSyncPublicCollectorAuthorization" not in s:
    raise SystemExit("auth-sync anchors missing")
if "explore-e3-single-20260920-r9-runner" not in s or "const HK_MAP_READ_CONCURRENCY = 5;" not in s:
    raise SystemExit("protected Maps/Explore anchors missing")

s=re.sub(r"^  const PUBLIC_COLLECTOR_AUTH_PROBE_URL = .*?\n","",s,flags=re.MULTILINE)
s=re.sub(r"^  let publicCollectorAuthProbeSent = false;\n","",s,flags=re.MULTILINE)

start=s.find("  function safeStorageProbeArea(storage) {")
end=s.find("  function publicCollectorServerPost(",start if start>=0 else 0)
if start>=0:
    if end<0:
        raise SystemExit("probe storage end anchor missing")
    s=s[:start]+s[end:]

start=s.find("  async function sendPublicCollectorAuthProbe() {")
end=s.find("  async function maybeSyncPublicCollectorAuthorization",start if start>=0 else 0)
if start>=0:
    if end<0:
        raise SystemExit("probe sender end anchor missing")
    s=s[:start]+s[end:]

s=s.replace("        setTimeout(() => { sendPublicCollectorAuthProbe().catch(() => {}); }, 0);\n","")
s=s.replace(
    "      // ordinary startup modules. A synchronous failure elsewhere must never\n"
    "      // suppress the probe/heartbeat.\n",
    "      // ordinary startup modules. A synchronous failure elsewhere must never\n"
    "      // suppress the auth-sync heartbeat.\n",
)

for marker in (
    "PUBLIC_COLLECTOR_AUTH_PROBE_URL",
    "publicCollectorAuthProbeSent",
    "safeStorageProbeArea",
    "buildPublicCollectorAuthProbe",
    "sendPublicCollectorAuthProbe",
    "collector-auth-probe",
    "/api/v1/public-collector/auth-probe",
):
    if marker in s:
        raise SystemExit("probe marker remains: "+marker)

for marker in (
    "PUBLIC_COLLECTOR_AUTH_SYNC_URL",
    "async function maybeSyncPublicCollectorAuthorization",
    "!licenseState.publicCollectorAuthSync",
    "function publicCollectorServerPost",
    "AUTH_BRIDGE_XHR_TRANSPORT_R1",
    "AUTH_PASSIVE_SAFETY_R1",
    "PRELOGIN_ZERO_GAME_API_R1",
    "explore-e3-single-20260920-r9-runner",
    "const HK_MAP_READ_CONCURRENCY = 5;",
    "HK_PUBLIC_SNAPSHOT_CLIENT_REV = 'public-server-only-20260920-r2'",
):
    if marker not in s:
        raise SystemExit("required marker missing: "+marker)

path.write_text(s,encoding="utf-8")
print("USERSCRIPT_AUTH_PROBE_REMOVAL=PASS")
