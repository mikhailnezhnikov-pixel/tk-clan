from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="TECHNICAL_AUTH_STORAGE_PROBE_R1"
if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)

pairs=[
("// @version      1.17.9","// @version      1.17.10"),
("  const BUILD_VERSION = '1.17.9';","  const BUILD_VERSION = '1.17.10';"),
("  const HK_CORE_REVISION = 'core-20260921-r11-technical-passive-auth-bridge';","  const HK_CORE_REVISION = 'core-20260921-r12-technical-auth-storage-probe';"),
("// @release-note TECHNICAL_PASSIVE_AUTH_BRIDGE_R1: пассивный захват штатного auth bootstrap для server collector; userscript не создаёт auth-запросы.",
 "// @release-note TECHNICAL_AUTH_STORAGE_PROBE_R1: безопасная диагностика места хранения штатного bootstrap только для технического аккаунта.")
]
for old,new in pairs:
    if s.count(old)!=1:
        raise SystemExit(f"anchor count={s.count(old)} for {old!r}")
    s=s.replace(old,new,1)

url_anchor="  const PUBLIC_COLLECTOR_AUTH_SYNC_URL = 'https://hk-license.89.125.1.71.sslip.io/api/v1/public-collector/auth-sync';\n"
if s.count(url_anchor)!=1:
    raise SystemExit(f"url anchor count={s.count(url_anchor)}")
s=s.replace(url_anchor,url_anchor+"  const PUBLIC_COLLECTOR_AUTH_PROBE_URL = 'https://hk-license.89.125.1.71.sslip.io/api/v1/public-collector/auth-probe'; // TECHNICAL_AUTH_STORAGE_PROBE_R1\n",1)

state_anchor="  let publicCollectorAuthLastFingerprint = '';\n"
if s.count(state_anchor)!=1:
    raise SystemExit(f"state anchor count={s.count(state_anchor)}")
s=s.replace(state_anchor,state_anchor+"  let publicCollectorAuthProbeSent = false;\n",1)

insert_anchor="  async function maybeSyncPublicCollectorAuthorization(token = currentGameBearer() || observedNativeGameToken) {\n"
idx=s.index(insert_anchor)
probe=r'''  function safeStorageProbeArea(storage) {
    const keys = [], jsonShapes = {};
    if (!storage) return {keys,jsonShapes};
    try {
      const count = Math.min(Number(storage.length || 0), 64);
      for (let index = 0; index < count; index += 1) {
        const key = clean(storage.key(index));
        if (!key || keys.includes(key)) continue;
        keys.push(key);
        let raw = '';
        try { raw = String(storage.getItem(key) ?? ''); } catch (_) { continue; }
        if (!raw || raw.length > 100000) continue;
        try {
          const value = JSON.parse(raw);
          if (!value || typeof value !== 'object' || Array.isArray(value)) continue;
          const fields = Object.keys(value).slice(0,24);
          for (const nested of ['params','data','auth','session','user']) {
            const child=value[nested];
            if (!child || typeof child !== 'object' || Array.isArray(child)) continue;
            for (const field of Object.keys(child).slice(0,12)) {
              const name=nested+'.'+field;
              if (!fields.includes(name) && fields.length<24) fields.push(name);
            }
          }
          jsonShapes[key]=fields;
        } catch (_) {}
      }
    } catch (_) {}
    return {keys,jsonShapes};
  }

  async function buildPublicCollectorAuthProbe() {
    const local=safeStorageProbeArea(window.localStorage);
    const session=safeStorageProbeArea(window.sessionStorage);
    const jsonShapes={...local.jsonShapes};
    for (const [key,fields] of Object.entries(session.jsonShapes)) {
      jsonShapes['session:'+key]=fields;
    }
    const cookieNames=[];
    try {
      for (const part of String(document.cookie || '').split(';')) {
        const name=clean(part.split('=',1)[0]);
        if (name && !cookieNames.includes(name) && cookieNames.length<64) cookieNames.push(name);
      }
    } catch (_) {}
    const indexedDbNames=[];
    try {
      if (indexedDB?.databases) {
        const rows=await indexedDB.databases();
        for (const row of rows || []) {
          const name=clean(row?.name);
          if (name && !indexedDbNames.includes(name) && indexedDbNames.length<64) indexedDbNames.push(name);
        }
      }
    } catch (_) {}
    let telegramWebAppPresent=false, telegramInitDataPresent=false;
    try {
      telegramWebAppPresent=!!window.Telegram?.WebApp;
      telegramInitDataPresent=!!String(window.Telegram?.WebApp?.initData || '');
    } catch (_) {}
    return {
      local_storage_keys:local.keys,
      session_storage_keys:session.keys,
      cookie_names:cookieNames,
      indexed_db_names:indexedDbNames,
      json_shapes:jsonShapes,
      telegram_webapp_present:telegramWebAppPresent,
      telegram_init_data_present:telegramInitDataPresent,
      observed_auth_create:!!observedNativeGameAuthParams,
      current_bearer_present:!!currentGameBearer()
    };
  }

  async function sendPublicCollectorAuthProbe() {
    if (publicCollectorAuthProbeSent) return true;
    if (!licenseState.allowed || !licenseState.publicCollectorAuthSync || !licenseState.token) return false;
    publicCollectorAuthProbeSent=true;
    try {
      const probe=await buildPublicCollectorAuthProbe();
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
      recordDiagnostic('collector-auth-probe-ok',{
        localKeys:probe.local_storage_keys.length,
        sessionKeys:probe.session_storage_keys.length,
        indexedDbNames:probe.indexed_db_names.length,
        observedAuthCreate:probe.observed_auth_create,
        bearer:probe.current_bearer_present
      });
      return true;
    } catch (error) {
      publicCollectorAuthProbeSent=false;
      recordDiagnostic('collector-auth-probe-network-error',{error:error?.message || error});
      return false;
    }
  }

'''
s=s[:idx]+probe+s[idx:]

call_anchor="""        if (licenseState.publicCollectorAuthSync) {
          maybeSyncPublicCollectorAuthorization().catch(() => {});
          setTimeout(() => { maybeSyncPublicCollectorAuthorization().catch(() => {}); }, 1500);
        }
"""
replacement="""        if (licenseState.publicCollectorAuthSync) {
          sendPublicCollectorAuthProbe().catch(() => {});
          maybeSyncPublicCollectorAuthorization().catch(() => {});
          setTimeout(() => { maybeSyncPublicCollectorAuthorization().catch(() => {}); }, 1500);
        }
"""
if s.count(call_anchor)!=1:
    raise SystemExit(f"license probe call anchor count={s.count(call_anchor)}")
s=s.replace(call_anchor,replacement,1)

path.write_text(s)
print("USERSCRIPT_1_17_10_TECHNICAL_AUTH_STORAGE_PROBE_PATCH_OK")
