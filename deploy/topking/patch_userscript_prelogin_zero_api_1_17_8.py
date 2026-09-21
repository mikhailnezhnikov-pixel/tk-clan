from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="PRELOGIN_ZERO_GAME_API_R1"
if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)

pairs=[
("// @version      1.17.7","// @version      1.17.8"),
("  const BUILD_VERSION = '1.17.7';","  const BUILD_VERSION = '1.17.8';"),
("  const HK_CORE_REVISION = 'core-20260921-r9-auth-passive-safety';","  const HK_CORE_REVISION = 'core-20260921-r10-prelogin-zero-api';"),
("// @release-note AUTH_PASSIVE_SAFETY_R1: userscript больше не вызывает /auth/create автоматически; только пассивно использует штатную авторизацию игры.",
 "// @release-note PRELOGIN_ZERO_GAME_API_R1: до успешного native login userscript не делает ни одного Game API запроса; Maps и Explore без изменений.")
]
for old,new in pairs:
    if s.count(old)!=1:
        raise SystemExit(f"anchor count={s.count(old)} for {old!r}")
    s=s.replace(old,new,1)

old_ready=s[s.index("  function hkNativeGameLoginReady() {"):s.index("\n  function startAfterNativeGameLogin()",s.index("  function hkNativeGameLoginReady() {"))]
new_ready="""  function hkNativeGameLoginReady() {
    // PRELOGIN_ZERO_GAME_API_R1
    // Fail closed. The gate opens only after the native game itself has made
    // an authenticated /player/me that our passive network observer captured.
    return !!(playerDocument && apiHeaders.Authorization);
  }
"""
s=s.replace(old_ready,new_ready,1)

old_start=s[s.index("  function startAfterNativeGameLogin() {"):s.index("\n  runtime.destroy = () => {",s.index("  function startAfterNativeGameLogin() {"))]
new_start="""  function startAfterNativeGameLogin() {
    if (hkNativeLoginRuntimeStarted) return;
    if (!hkNativeGameLoginReady()) {
      setTimeout(startAfterNativeGameLogin, 500);
      return;
    }
    hkNativeLoginRuntimeStarted = true;
    startInterface();
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', startInterface, {once:true});
    setInterval(() => {
      // PRELOGIN_ZERO_GAME_API_R1: observe only; never create/refresh the
      // native session and never bootstrap /player/me ourselves.
      refreshStoredGameAuthorization();
      const token=currentGameBearer();
      const ok=!!token && jwtExpiration(token)>Date.now()+5000;
      setHealth('auth', ok, ok ? 'авторизация активна' : 'ожидаю вход игры');
      if (ok && licenseState.publicCollectorAuthSync) maybeSyncPublicCollectorAuthorization(token).catch(() => {});
    }, 30000);
    setInterval(captureActiveEventCode, 1500);
    setTimeout(() => hkGameBridge.discover(false), 1500);
    setInterval(() => { if (!hkGameBridge.ready) hkGameBridge.discover(false); }, 30000);
    setInterval(() => { if (playerDocument) checkLicense(playerDocument.player || {}, true); }, LICENSE_RECHECK_MS);
    recordDiagnostic('native-login-gate-open',{revision:'prelogin-zero-game-api-r1'});
  }
"""
s=s.replace(old_start,new_start,1)

# Network observer may inspect native responses pre-login, but it must not
# schedule any bridge refresh/mutation before the native login gate is open.
old_fetch="""      if (response.ok && isGameApiRequest(url)) hkGameBridge.noteMutation(path, init?.method || input?.method || 'GET');
"""
new_fetch="""      if (hkNativeLoginRuntimeStarted && response.ok && isGameApiRequest(url)) hkGameBridge.noteMutation(path, init?.method || input?.method || 'GET');
"""
if s.count(old_fetch)!=1:
    raise SystemExit(f"fetch noteMutation anchor count={s.count(old_fetch)}")
s=s.replace(old_fetch,new_fetch,1)

old_xhr="""              hkGameBridge.noteMutation(path, this.__hkMethod || 'GET');
"""
new_xhr="""              if (hkNativeLoginRuntimeStarted) hkGameBridge.noteMutation(path, this.__hkMethod || 'GET');
"""
if s.count(old_xhr)!=1:
    raise SystemExit(f"xhr noteMutation anchor count={s.count(old_xhr)}")
s=s.replace(old_xhr,new_xhr,1)

# Remove automatic game API clan scan from the license-success startup path.
old_license="""        synchronizeSettings(); flushPitObservations(); loadSharedPitPowers(); refreshSharedClanSkills(); maybeAutoScanClanSkills();
"""
new_license="""        synchronizeSettings(); flushPitObservations(); loadSharedPitPowers(); refreshSharedClanSkills();
"""
if s.count(old_license)!=1:
    raise SystemExit(f"license startup anchor count={s.count(old_license)}")
s=s.replace(old_license,new_license,1)

old_tail="""  startInterface();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startInterface, {once:true});
  }
  startAfterNativeGameLogin();
  setInterval(() => {
    if (runtime.active) runtime.ensure?.();
  }, 1000);
"""
new_tail="""  // PRELOGIN_ZERO_GAME_API_R1: install only passive interception before login.
  // No UI, bootstrap or Game API calls are started until native /player/me was
  // observed successfully.
  startNetworkCapture();
  startAfterNativeGameLogin();
  setInterval(() => {
    if (hkNativeLoginRuntimeStarted && runtime.active) runtime.ensure?.();
  }, 1000);
"""
if s.count(old_tail)!=1:
    raise SystemExit(f"startup tail anchor count={s.count(old_tail)}")
s=s.replace(old_tail,new_tail,1)

path.write_text(s)
print("USERSCRIPT_1_17_8_PRELOGIN_ZERO_API_PATCH_OK")
