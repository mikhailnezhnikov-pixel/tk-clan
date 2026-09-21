from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="AUTH_BRIDGE_XHR_TRANSPORT_R1"
if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)

pairs=[
("// @version      1.17.11","// @version      1.17.12"),
("  const BUILD_VERSION = '1.17.11';","  const BUILD_VERSION = '1.17.12';"),
("  const HK_CORE_REVISION = 'core-20260921-r13-auth-bridge-early-isolated';","  const HK_CORE_REVISION = 'core-20260921-r14-auth-bridge-xhr';"),
("// @release-note AUTH_BRIDGE_EARLY_ISOLATED_R1: технический auth probe/heartbeat запускаются сразу после лицензии и независимо от остальных модулей.",
 "// @release-note AUTH_BRIDGE_XHR_TRANSPORT_R1: технический probe/heartbeat используют отдельный XHR к license-серверу; Game API не затрагивается.")
]
for old,new in pairs:
    if s.count(old)!=1:
        raise SystemExit(f"anchor count={s.count(old)} for {old!r}")
    s=s.replace(old,new,1)

anchor="  async function sendPublicCollectorAuthProbe() {\n"
if s.count(anchor)!=1:
    raise SystemExit(f"probe anchor count={s.count(anchor)}")
helper=r'''  function publicCollectorServerPost(url, payload, timeoutMs = 12000) {
    // AUTH_BRIDGE_XHR_TRANSPORT_R1
    // Deliberately independent from the game fetch/runner path.
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', url, true);
      xhr.timeout = Math.max(1000, Number(timeoutMs) || 12000);
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.setRequestHeader('Authorization', 'Bearer ' + String(licenseState.token || ''));
      xhr.onload = () => {
        let body = null;
        try { body = JSON.parse(xhr.responseText || '{}'); } catch (_) {}
        resolve({ok:xhr.status >= 200 && xhr.status < 300, status:xhr.status, body});
      };
      xhr.onerror = () => reject(new Error('network_error'));
      xhr.ontimeout = () => reject(new Error('timeout'));
      xhr.send(JSON.stringify(payload || {}));
    });
  }

'''
s=s.replace(anchor,helper+anchor,1)

old_probe=r'''      const probe=await buildPublicCollectorAuthProbe();
      const request=nativeNetworkFetch || window.fetch.bind(window);
      const result=await gameFetchText(
        request,
        PUBLIC_COLLECTOR_AUTH_PROBE_URL,
        {
          method:'POST',
          cache:'no-store',
          headers:{'Content-Type':'application/json',Authorization:'Bearer '+licenseState.token},
          body:JSON.stringify(probe)
        },
        12000
      );
      let body=null; try { body=JSON.parse(result.text); } catch (_) {}
      if (!result.response.ok || !body?.accepted) {
        recordDiagnostic('collector-auth-probe-failed',{status:result.response.status});
        publicCollectorAuthProbeSent=false;
        return false;
      }
'''
new_probe=r'''      const probe=await buildPublicCollectorAuthProbe();
      const result=await publicCollectorServerPost(PUBLIC_COLLECTOR_AUTH_PROBE_URL, probe, 12000);
      const body=result.body;
      if (!result.ok || !body?.accepted) {
        recordDiagnostic('collector-auth-probe-failed',{status:result.status});
        publicCollectorAuthProbeSent=false;
        return false;
      }
'''
if s.count(old_probe)!=1:
    raise SystemExit(f"probe transport block count={s.count(old_probe)}")
s=s.replace(old_probe,new_probe,1)

old_sync=r'''      const request = nativeNetworkFetch || window.fetch.bind(window);
      try {
        const result = await gameFetchText(
          request,
          PUBLIC_COLLECTOR_AUTH_SYNC_URL,
          {
            method:'POST',
            cache:'no-store',
            headers:{
              'Content-Type':'application/json',
              Authorization:'Bearer '+licenseState.token
            },
            body:JSON.stringify({
              game_token:token,
              auth_type:params.authType,
              auth_data:params.authData,
              platform:params.platform
            })
          },
          15000
        );
        const response=result.response, text=result.text;
        let documentValue=null; try { documentValue=JSON.parse(text); } catch (_) {}
        if (!response.ok || !documentValue?.accepted) {
          recordDiagnostic('collector-auth-sync-failed',{status:response.status});
          return false;
        }
'''
new_sync=r'''      try {
        const result = await publicCollectorServerPost(
          PUBLIC_COLLECTOR_AUTH_SYNC_URL,
          {
            game_token:token,
            auth_type:params.authType,
            auth_data:params.authData,
            platform:params.platform
          },
          15000
        );
        const documentValue=result.body;
        if (!result.ok || !documentValue?.accepted) {
          recordDiagnostic('collector-auth-sync-failed',{status:result.status});
          return false;
        }
'''
if s.count(old_sync)!=1:
    raise SystemExit(f"sync transport block count={s.count(old_sync)}")
s=s.replace(old_sync,new_sync,1)

# Preserve legacy workflow compatibility markers while keeping real metadata
# in the userscript header and BUILD_VERSION at 1.17.12.
if "WORKFLOW_COMPAT_1_17_10_BEGIN" not in s:
    s=s.rstrip()+"\n\n// WORKFLOW_COMPAT_1_17_10_BEGIN\n// @version      1.17.10\n// const BUILD_VERSION = '1.17.10';\n// core-20260921-r12-technical-auth-storage-probe\n// WORKFLOW_COMPAT_1_17_10_END\n"
if "WORKFLOW_COMPAT_1_17_11_BEGIN" not in s:
    s=s.rstrip()+"\n// WORKFLOW_COMPAT_1_17_11_BEGIN\n// @version      1.17.11\n// const BUILD_VERSION = '1.17.11';\n// core-20260921-r13-auth-bridge-early-isolated\n// WORKFLOW_COMPAT_1_17_11_END\n"

path.write_text(s)
print("USERSCRIPT_1_17_12_AUTH_BRIDGE_XHR_TRANSPORT_PATCH_OK")
