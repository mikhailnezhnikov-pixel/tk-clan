from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="PUBLIC_COLLECTOR_NATIVE_AUTH_OBSERVER_R1"
if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)

replacements=[
    ("// @version      1.17.5","// @version      1.17.6"),
    ("  const BUILD_VERSION = '1.17.5';","  const BUILD_VERSION = '1.17.6';"),
    ("  const HK_CORE_REVISION = 'core-20260921-r7-auth-heartbeat';","  const HK_CORE_REVISION = 'core-20260921-r8-native-auth-observer';"),
    ("// @release-note Автоматическое обновление авторизации серверного public collector для технического аккаунта; Maps и Explore без изменений.",
     "// @release-note Надёжный захват штатного /auth/create для автоматического server collector auth; Maps и Explore без изменений."),
]
for old,new in replacements:
    if s.count(old)!=1:
        raise SystemExit(f"anchor count={s.count(old)} for {old!r}")
    s=s.replace(old,new,1)

state_anchor="  let publicCollectorAuthLastFingerprint = '';\n"
if s.count(state_anchor)!=1:
    raise SystemExit(f"state anchor count={s.count(state_anchor)}")
s=s.replace(state_anchor,state_anchor+"  let observedNativeGameAuthParams = null; // PUBLIC_COLLECTOR_NATIVE_AUTH_OBSERVER_R1\n",1)

read_old="""  function readNativeGameAuthParams() {
    try {
      const webApp = window.Telegram?.WebApp;
      const initData = String(webApp?.initData || '');
      if (webApp && webApp.platform && webApp.platform !== 'unknown' && initData) {
        return {authType:'MiniApp', authData:initData.replaceAll('&','%26'), platform:'TG', source:'telegram'};
      }
    } catch (_) {}
    try {
      const stored = JSON.parse(localStorage.getItem('auth-data') || 'null');
      const authType = clean(stored?.params?.auth_type);
      const authData = clean(stored?.params?.auth_data);
      const remembered = clean(localStorage.getItem('remember-me'));
      if (!authType || !authData || remembered !== authType) return null;
      return {authType, authData, platform:'WEB', source:'browser'};
    } catch (_) { return null; }
  }
"""
read_new="""  function authParamsFromUrl(url, source = 'network') {
    try {
      const parsed = new URL(String(url || ''), location.href);
      if (parsed.pathname !== '/auth/create') return null;
      const authType = clean(parsed.searchParams.get('auth_type'));
      const authData = clean(parsed.searchParams.get('auth_data'));
      const platform = clean(parsed.searchParams.get('platform'));
      if (!authType || !authData || !platform) return null;
      return {authType, authData, platform, source};
    } catch (_) { return null; }
  }

  function captureNativeGameAuthParams(url) {
    const params = authParamsFromUrl(url, 'network');
    if (!params) return false;
    observedNativeGameAuthParams = params;
    return true;
  }

  function readNativeGameAuthParams() {
    try {
      const webApp = window.Telegram?.WebApp;
      const initData = String(webApp?.initData || '');
      if (webApp && webApp.platform && webApp.platform !== 'unknown' && initData) {
        return {authType:'MiniApp', authData:initData.replaceAll('&','%26'), platform:'TG', source:'telegram'};
      }
    } catch (_) {}

    if (observedNativeGameAuthParams?.authType && observedNativeGameAuthParams?.authData && observedNativeGameAuthParams?.platform) {
      return {...observedNativeGameAuthParams};
    }

    try {
      const stored = JSON.parse(localStorage.getItem('auth-data') || 'null');
      const authType = clean(stored?.params?.auth_type);
      const authData = clean(stored?.params?.auth_data);
      const remembered = clean(localStorage.getItem('remember-me'));
      if (authType && authData && remembered === authType) {
        return {authType, authData, platform:'WEB', source:'browser'};
      }
    } catch (_) {}

    try {
      const entries = performance.getEntriesByType('resource').slice().reverse();
      for (const entry of entries) {
        const params = authParamsFromUrl(entry?.name, 'performance');
        if (!params) continue;
        observedNativeGameAuthParams = params;
        return {...params};
      }
    } catch (_) {}

    return null;
  }
"""
if s.count(read_old)!=1:
    raise SystemExit(f"readNativeGameAuthParams anchor count={s.count(read_old)}")
s=s.replace(read_old,read_new,1)

fetch_old="""    window.fetch = async function(input, init) {
      const url = typeof input === 'string' ? input : input?.url;
      const requestHeaders = {...headersToObject(input?.headers), ...headersToObject(init?.headers)};
      captureAuthorization(url, requestHeaders);
"""
fetch_new="""    window.fetch = async function(input, init) {
      const url = typeof input === 'string' ? input : input?.url;
      const requestHeaders = {...headersToObject(input?.headers), ...headersToObject(init?.headers)};
      captureNativeGameAuthParams(url);
      captureAuthorization(url, requestHeaders);
"""
if s.count(fetch_old)!=1:
    raise SystemExit(f"fetch anchor count={s.count(fetch_old)}")
s=s.replace(fetch_old,fetch_new,1)

xhr_old="""    XMLHttpRequest.prototype.open = function(method, url, ...rest) {
      this.__hkUrl = url; this.__hkMethod = method; this.__hkHeaders = {};
      return open.call(this, method, url, ...rest);
    };
"""
xhr_new="""    XMLHttpRequest.prototype.open = function(method, url, ...rest) {
      this.__hkUrl = url; this.__hkMethod = method; this.__hkHeaders = {};
      captureNativeGameAuthParams(url);
      return open.call(this, method, url, ...rest);
    };
"""
if s.count(xhr_old)!=1:
    raise SystemExit(f"xhr anchor count={s.count(xhr_old)}")
s=s.replace(xhr_old,xhr_new,1)

# On license success, try once after a short delay as well. By then the game's
# initial auth/create resource is usually present in PerformanceResourceTiming.
post_old="""        if (licenseState.publicCollectorAuthSync) maybeSyncPublicCollectorAuthorization().catch(() => {});
"""
post_new="""        if (licenseState.publicCollectorAuthSync) {
          maybeSyncPublicCollectorAuthorization().catch(() => {});
          setTimeout(() => { maybeSyncPublicCollectorAuthorization().catch(() => {}); }, 1500);
        }
"""
if s.count(post_old)!=1:
    raise SystemExit(f"post-license heartbeat anchor count={s.count(post_old)}")
s=s.replace(post_old,post_new,1)

assert MARKER in s
path.write_text(s)
print("USERSCRIPT_1_17_6_NATIVE_AUTH_OBSERVER_PATCH_OK")
