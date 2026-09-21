from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="TECHNICAL_PASSIVE_AUTH_BRIDGE_R1"
if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)

pairs=[
("// @version      1.17.8","// @version      1.17.9"),
("  const BUILD_VERSION = '1.17.8';","  const BUILD_VERSION = '1.17.9';"),
("  const HK_CORE_REVISION = 'core-20260921-r10-prelogin-zero-api';","  const HK_CORE_REVISION = 'core-20260921-r11-technical-passive-auth-bridge';"),
("// @release-note PRELOGIN_ZERO_GAME_API_R1: до успешного native login userscript не делает ни одного Game API запроса; Maps и Explore без изменений.",
 "// @release-note TECHNICAL_PASSIVE_AUTH_BRIDGE_R1: пассивный захват штатного auth bootstrap для server collector; userscript не создаёт auth-запросы.")
]
for old,new in pairs:
    if s.count(old)!=1:
        raise SystemExit(f"anchor count={s.count(old)} for {old!r}")
    s=s.replace(old,new,1)

state_anchor="  let observedNativeGameAuthParams = null; // PUBLIC_COLLECTOR_NATIVE_AUTH_OBSERVER_R1\n"
if s.count(state_anchor)!=1:
    raise SystemExit(f"state anchor count={s.count(state_anchor)}")
s=s.replace(state_anchor,state_anchor+"  let observedNativeGameToken = ''; // TECHNICAL_PASSIVE_AUTH_BRIDGE_R1\n",1)

start=s.index("  function authParamsFromUrl(url, source = 'network') {")
end=s.index("\n  async function maybeSyncPublicCollectorAuthorization",start)
old=s[start:end]
new=r'''  function authParamsFromUrl(url, source = 'network-url') {
    try {
      const parsed = new URL(String(url || ''), location.href);
      if (parsed.pathname !== '/auth/create') return null;
      const authType = clean(parsed.searchParams.get('auth_type') || parsed.searchParams.get('authType'));
      const authData = clean(parsed.searchParams.get('auth_data') || parsed.searchParams.get('authData'));
      const platform = clean(parsed.searchParams.get('platform'));
      if (!authType || !authData || !platform) return null;
      return {authType, authData, platform, source};
    } catch (_) { return null; }
  }

  function authParamsFromBody(body, source = 'network-body') {
    if (body == null) return null;
    let value = body;
    try {
      if (typeof FormData !== 'undefined' && body instanceof FormData) {
        value = Object.fromEntries(body.entries());
      } else if (typeof URLSearchParams !== 'undefined' && body instanceof URLSearchParams) {
        value = Object.fromEntries(body.entries());
      } else if (typeof body === 'string') {
        try { value = JSON.parse(body); }
        catch (_) { value = Object.fromEntries(new URLSearchParams(body).entries()); }
      }
    } catch (_) { return null; }
    if (!value || typeof value !== 'object') return null;
    const authType = clean(value.auth_type ?? value.authType);
    const authData = clean(value.auth_data ?? value.authData);
    const platform = clean(value.platform);
    if (!authType || !authData || !platform) return null;
    return {authType, authData, platform, source};
  }

  function captureNativeGameAuthParams(url, body = null, source = 'network') {
    let path = '';
    try { path = new URL(String(url || ''), location.href).pathname; } catch (_) {}
    if (path !== '/auth/create') return false;
    const params = authParamsFromUrl(url, `${source}-url`) || authParamsFromBody(body, `${source}-body`);
    if (!params) return false;
    observedNativeGameAuthParams = params;
    return true;
  }

  function captureNativeGameAuthToken(documentValue) {
    const token = clean(documentValue?.token);
    if (!token || jwtExpiration(token) <= Date.now() + 5000) return false;
    observedNativeGameToken = token;
    return true;
  }

  function readNativeGameAuthParams() {
    if (observedNativeGameAuthParams?.authType && observedNativeGameAuthParams?.authData && observedNativeGameAuthParams?.platform) {
      return {...observedNativeGameAuthParams};
    }

    try {
      const webApp = window.Telegram?.WebApp;
      const initData = String(webApp?.initData || '');
      if (webApp && webApp.platform && webApp.platform !== 'unknown' && initData) {
        return {authType:'MiniApp', authData:initData.replaceAll('&','%26'), platform:'TG', source:'telegram-passive'};
      }
    } catch (_) {}

    try {
      const stored = JSON.parse(localStorage.getItem('auth-data') || 'null');
      const authType = clean(stored?.params?.auth_type);
      const authData = clean(stored?.params?.auth_data);
      const platform = clean(stored?.params?.platform || 'WEB');
      const remembered = clean(localStorage.getItem('remember-me'));
      if (authType && authData && remembered === authType) {
        return {authType, authData, platform, source:'browser-storage-passive'};
      }
    } catch (_) {}

    try {
      const entries = performance.getEntriesByType('resource').slice().reverse();
      for (const entry of entries) {
        const params = authParamsFromUrl(entry?.name, 'performance-passive');
        if (!params) continue;
        observedNativeGameAuthParams = params;
        return {...params};
      }
    } catch (_) {}

    return null;
  }
'''
s=s[:start]+new+s[end:]

old_sig="  async function maybeSyncPublicCollectorAuthorization(token = currentGameBearer()) {"
new_sig="  async function maybeSyncPublicCollectorAuthorization(token = currentGameBearer() || observedNativeGameToken) {"
if s.count(old_sig)!=1:
    raise SystemExit(f"heartbeat signature count={s.count(old_sig)}")
s=s.replace(old_sig,new_sig,1)

a=s.index("  async function refreshGoogleAuthData(params) {")
b=s.index("\n  async function ensureGameAuthorization",a)
new_active=r'''  async function refreshGoogleAuthData(params) {
    // TECHNICAL_PASSIVE_AUTH_BRIDGE_R1: never prompt or refresh Google auth.
    return params || null;
  }

  async function checkGameBearer(token) {
    // TECHNICAL_PASSIVE_AUTH_BRIDGE_R1: local expiry check only; no /auth/check.
    return !!token && jwtExpiration(token) > Date.now() + 5000;
  }

  async function createFreshGameAuthorization(reason = 'refresh', expectedToken = '') {
    // TECHNICAL_PASSIVE_AUTH_BRIDGE_R1: native game exclusively owns /auth/create.
    recordDiagnostic('auth-create-blocked-passive-only',{reason});
    return '';
  }
'''
s=s[:a]+new_active+s[b:]

fetch_old="""      const requestHeaders = {...headersToObject(input?.headers), ...headersToObject(init?.headers)};
      captureNativeGameAuthParams(url);
      captureAuthorization(url, requestHeaders);
      const response = await nativeFetch(input, init);
      const path = url ? new URL(url, location.href).pathname : '';
"""
fetch_new="""      const requestHeaders = {...headersToObject(input?.headers), ...headersToObject(init?.headers)};
      captureNativeGameAuthParams(url, init?.body, 'fetch');
      if (!observedNativeGameAuthParams && typeof Request !== 'undefined' && input instanceof Request) {
        try { input.clone().text().then(body => captureNativeGameAuthParams(url, body, 'fetch-request')).catch(() => {}); } catch (_) {}
      }
      captureAuthorization(url, requestHeaders);
      const response = await nativeFetch(input, init);
      const path = url ? new URL(url, location.href).pathname : '';
      if (path === '/auth/create' && response.ok) {
        response.clone().json().then(body => captureNativeGameAuthToken(body)).catch(() => {});
      }
"""
if s.count(fetch_old)!=1:
    raise SystemExit(f"fetch capture anchor count={s.count(fetch_old)}")
s=s.replace(fetch_old,fetch_new,1)

xhr_open_old="""      this.__hkUrl = url; this.__hkMethod = method; this.__hkHeaders = {};
      captureNativeGameAuthParams(url);
      return open.call(this, method, url, ...rest);
"""
xhr_open_new="""      this.__hkUrl = url; this.__hkMethod = method; this.__hkHeaders = {};
      captureNativeGameAuthParams(url, null, 'xhr-open');
      return open.call(this, method, url, ...rest);
"""
if s.count(xhr_open_old)!=1:
    raise SystemExit(f"xhr open anchor count={s.count(xhr_open_old)}")
s=s.replace(xhr_open_old,xhr_open_new,1)

xhr_send_old="""    XMLHttpRequest.prototype.send = function(...args) {
      if (this.__hkUrl) captureAuthorization(this.__hkUrl, this.__hkHeaders);
      if (this.__hkUrl && isGameApiRequest(this.__hkUrl)) {
"""
xhr_send_new="""    XMLHttpRequest.prototype.send = function(...args) {
      if (this.__hkUrl) {
        captureNativeGameAuthParams(this.__hkUrl, args[0], 'xhr-send');
        captureAuthorization(this.__hkUrl, this.__hkHeaders);
      }
      if (this.__hkUrl && isGameApiRequest(this.__hkUrl)) {
"""
if s.count(xhr_send_old)!=1:
    raise SystemExit(f"xhr send anchor count={s.count(xhr_send_old)}")
s=s.replace(xhr_send_old,xhr_send_new,1)

xhr_body_old="""              const body = JSON.parse(this.responseText);
              if (hkNativeLoginRuntimeStarted) hkGameBridge.noteMutation(path, this.__hkMethod || 'GET');
"""
xhr_body_new="""              const body = JSON.parse(this.responseText);
              if (path === '/auth/create') captureNativeGameAuthToken(body);
              if (hkNativeLoginRuntimeStarted) hkGameBridge.noteMutation(path, this.__hkMethod || 'GET');
"""
if s.count(xhr_body_old)!=1:
    raise SystemExit(f"xhr response anchor count={s.count(xhr_body_old)}")
s=s.replace(xhr_body_old,xhr_body_new,1)

path.write_text(s)
print("USERSCRIPT_1_17_9_TECHNICAL_PASSIVE_AUTH_BRIDGE_PATCH_OK")
