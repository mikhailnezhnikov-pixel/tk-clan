from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="PUBLIC_COLLECTOR_AUTH_HEARTBEAT_CLIENT_R1"
if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)

const_anchor="  const PUBLIC_SNAPSHOT_API = 'https://hk-license.89.125.1.71.sslip.io/api/v1/public-snapshot';\n"
if s.count(const_anchor)!=1:
    raise SystemExit(f"const anchor count={s.count(const_anchor)}")
s=s.replace(const_anchor,const_anchor+"""  const PUBLIC_COLLECTOR_AUTH_HEARTBEAT_REV = 'public-collector-auth-heartbeat-20260921-r1'; // PUBLIC_COLLECTOR_AUTH_HEARTBEAT_CLIENT_R1
  const PUBLIC_COLLECTOR_AUTH_SYNC_URL = 'https://hk-license.89.125.1.71.sslip.io/api/v1/public-collector/auth-sync';
""",1)

state_anchor="  let authCreatePromise = null;\n"
if s.count(state_anchor)!=1:
    raise SystemExit(f"state anchor count={s.count(state_anchor)}")
s=s.replace(state_anchor,state_anchor+"""  let publicCollectorAuthSyncPromise = null;
  let publicCollectorAuthLastFingerprint = '';
""",1)

license_state_old="  let licenseState = {checked:false, allowed:false, playerId:'', reason:'Проверка лицензии…', update:null};"
license_state_new="  let licenseState = {checked:false, allowed:false, playerId:'', reason:'Проверка лицензии…', update:null, publicCollectorAuthSync:false};"
if s.count(license_state_old)!=1:
    raise SystemExit(f"license state anchor count={s.count(license_state_old)}")
s=s.replace(license_state_old,license_state_new,1)

capture_old="""    apiBase = resolvedUrl.origin;
    apiHeaders = {Authorization: auth[1], Accept: 'application/json, text/plain, */*', 'Content-Type': 'application/json'};
    authUpdatedAt = Date.now();
    return true;
"""
capture_new="""    const previousAuthorization = String(apiHeaders.Authorization || '');
    apiBase = resolvedUrl.origin;
    apiHeaders = {Authorization: auth[1], Accept: 'application/json, text/plain, */*', 'Content-Type': 'application/json'};
    authUpdatedAt = Date.now();
    if (previousAuthorization !== String(apiHeaders.Authorization || '') && licenseState?.publicCollectorAuthSync) {
      setTimeout(() => { maybeSyncPublicCollectorAuthorization().catch(() => {}); }, 0);
    }
    return true;
"""
if s.count(capture_old)!=1:
    raise SystemExit(f"capture anchor count={s.count(capture_old)}")
s=s.replace(capture_old,capture_new,1)

refresh_anchor="  async function refreshGoogleAuthData(params) {\n"
if s.count(refresh_anchor)!=1:
    raise SystemExit(f"refresh anchor count={s.count(refresh_anchor)}")
heartbeat=r'''  async function maybeSyncPublicCollectorAuthorization(token = currentGameBearer()) {
    token = clean(token);
    if (!licenseState.allowed || !licenseState.publicCollectorAuthSync || !licenseState.token || !token) return false;
    const expiresAt = jwtExpiration(token);
    if (expiresAt && expiresAt <= Date.now() + 5000) return false;
    const fingerprint = diagnosticFingerprint(token);
    if (fingerprint && fingerprint === publicCollectorAuthLastFingerprint) return true;
    if (publicCollectorAuthSyncPromise) return publicCollectorAuthSyncPromise;
    publicCollectorAuthSyncPromise = (async () => {
      const params = readNativeGameAuthParams();
      if (!params?.authType || !params?.authData || !params?.platform) {
        recordDiagnostic('collector-auth-sync-skipped',{reason:'bootstrap-unavailable'});
        return false;
      }
      const request = nativeNetworkFetch || window.fetch.bind(window);
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
        publicCollectorAuthLastFingerprint=fingerprint;
        recordDiagnostic('collector-auth-sync-ok',{expiresAt:expiresAt||null,authType:params.authType,platform:params.platform});
        return true;
      } catch (error) {
        recordDiagnostic('collector-auth-sync-network-error',{error:error?.message || error});
        return false;
      }
    })();
    try { return await publicCollectorAuthSyncPromise; }
    finally { publicCollectorAuthSyncPromise=null; }
  }

'''
s=s.replace(refresh_anchor,heartbeat+refresh_anchor,1)

create_old="""        setHealth('auth', true, 'токен обновлён');
        recordDiagnostic('auth-create-success',{reason, fingerprint:diagnosticFingerprint(token), playerId:gameBearerPlayerId(token), expiresAt:jwtExpiration(token)});
        return token;
"""
create_new="""        setHealth('auth', true, 'токен обновлён');
        recordDiagnostic('auth-create-success',{reason, fingerprint:diagnosticFingerprint(token), playerId:gameBearerPlayerId(token), expiresAt:jwtExpiration(token)});
        setTimeout(() => { maybeSyncPublicCollectorAuthorization(token).catch(() => {}); }, 0);
        return token;
"""
if s.count(create_old)!=1:
    raise SystemExit(f"create success anchor count={s.count(create_old)}")
s=s.replace(create_old,create_new,1)

allowed_line="? {checked:true, allowed:true, playerId, reason:'Доступ разрешён', token:String(body.token || ''), update:body.update || null}"
allowed_new="? {checked:true, allowed:true, playerId, reason:'Доступ разрешён', token:String(body.token || ''), update:body.update || null, publicCollectorAuthSync:!!body.public_collector_auth_sync}"
if s.count(allowed_line)!=1:
    raise SystemExit(f"allowed line count={s.count(allowed_line)}")
s=s.replace(allowed_line,allowed_new,1)

denied_line=": {checked:true, allowed:false, playerId, reason:licenseReason(body.reason || "
denied_i=s.find(denied_line)
if denied_i<0:
    raise SystemExit("denied object anchor missing")
denied_end=s.find("};",denied_i)
if denied_end<0:
    raise SystemExit("denied object end missing")
segment=s[denied_i:denied_end+2]
if "publicCollectorAuthSync" not in segment:
    segment_new=segment[:-2].rstrip()
    if segment_new.endswith("}"):
        segment_new=segment_new[:-1]+", publicCollectorAuthSync:false}"
    segment_new += ";"
    s=s[:denied_i]+segment_new+s[denied_end+2:]

post_license_old="""      if (licenseState.allowed) setTimeout(() => {
        synchronizeSettings(); flushPitObservations(); loadSharedPitPowers(); refreshSharedClanSkills(); maybeAutoScanClanSkills();
      }, 0);
"""
post_license_new="""      if (licenseState.allowed) setTimeout(() => {
        synchronizeSettings(); flushPitObservations(); loadSharedPitPowers(); refreshSharedClanSkills(); maybeAutoScanClanSkills();
        if (licenseState.publicCollectorAuthSync) maybeSyncPublicCollectorAuthorization().catch(() => {});
      }, 0);
"""
if s.count(post_license_old)!=1:
    raise SystemExit(f"post license anchor count={s.count(post_license_old)}")
s=s.replace(post_license_old,post_license_new,1)

assert MARKER in s
path.write_text(s)
print("PUBLIC_COLLECTOR_AUTH_HEARTBEAT_CLIENT_R1_PATCH_OK")
