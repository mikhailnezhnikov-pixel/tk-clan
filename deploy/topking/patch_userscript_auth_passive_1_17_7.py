from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="AUTH_PASSIVE_SAFETY_R1"
if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)

pairs=[
("// @version      1.17.6","// @version      1.17.7"),
("  const BUILD_VERSION = '1.17.6';","  const BUILD_VERSION = '1.17.7';"),
("  const HK_CORE_REVISION = 'core-20260921-r8-native-auth-observer';","  const HK_CORE_REVISION = 'core-20260921-r9-auth-passive-safety';"),
("// @release-note Надёжный захват штатного /auth/create для автоматического server collector auth; Maps и Explore без изменений.",
 "// @release-note AUTH_PASSIVE_SAFETY_R1: userscript больше не вызывает /auth/create автоматически; только пассивно использует штатную авторизацию игры.")
]
for old,new in pairs:
    if s.count(old)!=1:
        raise SystemExit(f"anchor count={s.count(old)} for {old!r}")
    s=s.replace(old,new,1)

old_ensure="""  async function ensureGameAuthorization(force = false, reason = 'runtime') {
    restoreGameApiBaseFromPerformance();
    if (!apiBase) apiBase = GAME_API_FALLBACK;
    refreshStoredGameAuthorization();
    let token = currentGameBearer();
    const expiresAt = jwtExpiration(token);
    if (!force && token && expiresAt > Date.now() + GAME_AUTH_REFRESH_EARLY_MS) {
      setHealth('auth', true, 'токен активен');
      return true;
    }
    if (token && !force && expiresAt > Date.now() + 5000) {
      const valid = await checkGameBearer(token);
      if (valid) { setHealth('auth', true, 'токен проверен'); return true; }
    }
    const fresh = await createFreshGameAuthorization(reason, token);
    token = fresh || currentGameBearer();
    const ok = !!token && jwtExpiration(token) > Date.now() + 5000;
    setHealth('auth', ok, ok ? 'авторизация активна' : 'нужен повторный вход');
    return ok;
  }
"""
new_ensure="""  async function ensureGameAuthorization(force = false, reason = 'runtime') {
    // AUTH_PASSIVE_SAFETY_R1
    // Never create or refresh a game session from the userscript. The native
    // game owns /auth/create. We only consume a bearer already issued by it.
    restoreGameApiBaseFromPerformance();
    if (!apiBase) apiBase = GAME_API_FALLBACK;
    refreshStoredGameAuthorization();
    const token = currentGameBearer();
    const ok = !!token && jwtExpiration(token) > Date.now() + 5000;
    setHealth('auth', ok, ok ? 'авторизация активна' : 'ожидаю вход игры');
    return ok;
  }
"""
if s.count(old_ensure)!=1:
    raise SystemExit(f"ensure auth anchor count={s.count(old_ensure)}")
s=s.replace(old_ensure,new_ensure,1)

old_timer="""    setInterval(() => { ensureGameAuthorization(false, 'background').catch(error => recordDiagnostic('auth-background-error',{error:error?.message || error})); }, 30000);
"""
new_timer="""    setInterval(() => {
      // AUTH_PASSIVE_SAFETY_R1: observe only; never call /auth/create here.
      refreshStoredGameAuthorization();
      const token=currentGameBearer();
      const ok=!!token && jwtExpiration(token)>Date.now()+5000;
      setHealth('auth', ok, ok ? 'авторизация активна' : 'ожидаю вход игры');
      if (ok && licenseState.publicCollectorAuthSync) maybeSyncPublicCollectorAuthorization(token).catch(() => {});
    }, 30000);
"""
if s.count(old_timer)!=1:
    raise SystemExit(f"background timer anchor count={s.count(old_timer)}")
s=s.replace(old_timer,new_timer,1)

path.write_text(s)
print("USERSCRIPT_1_17_7_AUTH_PASSIVE_SAFETY_PATCH_OK")
