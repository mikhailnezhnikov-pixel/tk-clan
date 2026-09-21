from pathlib import Path

PATH = Path("/tmp/HamsterKingMobile.user.js")
s = PATH.read_text(encoding="utf-8")

required = [
    "// @version      1.17.12",
    "const BUILD_VERSION = '1.17.12';",
    "const HK_CORE_REVISION = 'core-20260921-r14-auth-bridge-xhr';",
    "function hkNativeGameLoginReady()",
    "function startAfterNativeGameLogin()",
    "// PRELOGIN_ZERO_GAME_API_R1: install only passive interception before login.",
    "createFreshGameAuthorization(reason = 'refresh'",
]
for marker in required:
    if marker not in s:
        raise SystemExit(f"missing expected marker: {marker}")

if "/auth/create" not in s:
    raise SystemExit("expected passive auth observer markers missing")

s = s.replace("// @version      1.17.12", "// @version      1.17.13", 1)
s = s.replace(
    "// @release-note Исправлена проверка авторизации после входа в игру.",
    "// @release-note Исправлено подключение HK, если игра уже успела авторизоваться до запуска панели.\n"
    "// @release-note Исправлена проверка авторизации после входа в игру.",
    1,
)
s = s.replace("const BUILD_VERSION = '1.17.12';", "const BUILD_VERSION = '1.17.13';", 1)
s = s.replace(
    "const HK_CORE_REVISION = 'core-20260921-r14-auth-bridge-xhr';",
    "const HK_CORE_REVISION = 'core-20260921-r15-late-login-handoff';",
    1,
)
s = s.replace("bootstrapButton.textContent = problem ? 'HK!' : 'HK6';", "bootstrapButton.textContent = problem ? 'HK!' : 'HK…';", 1)

old = """  // HK_NATIVE_LOGIN_GATE_V1 login-gate-20260920-r1
  const HK_NATIVE_LOGIN_GATE_REV = 'login-gate-hotfix-20260920-r2';
  const HK_UI_PRELOGIN_REV = 'ui-prelogin-20260920-r3';
  const HK_LAUNCHER_HANDOFF_REV = 'launcher-handoff-20260920-r4';
  let hkNativeLoginRuntimeStarted = false;

  function hkNativeGameLoginReady() {
    // PRELOGIN_ZERO_GAME_API_R1
    // Fail closed. The gate opens only after the native game itself has made
    // an authenticated /player/me that our passive network observer captured.
    return !!(playerDocument && apiHeaders.Authorization);
  }

  function startAfterNativeGameLogin() {
    if (hkNativeLoginRuntimeStarted) return;
    if (!hkNativeGameLoginReady()) {
      setTimeout(startAfterNativeGameLogin, 500);
      return;
    }
    hkNativeLoginRuntimeStarted = true;
"""
new = """  // HK_NATIVE_LOGIN_GATE_V1 login-gate-20260920-r1
  const HK_NATIVE_LOGIN_GATE_REV = 'login-gate-hotfix-20260920-r2';
  const HK_UI_PRELOGIN_REV = 'ui-prelogin-20260920-r3';
  const HK_LAUNCHER_HANDOFF_REV = 'launcher-handoff-20260920-r4';
  const HK_LATE_LOGIN_HANDOFF_REV = 'late-login-handoff-20260921-r1';
  let hkNativeLoginRuntimeStarted = false;
  let hkLateLoginHandoffAttempts = 0;
  let hkLateLoginHandoffBusy = false;
  let hkLateLoginHandoffNextAt = 0;
  const hkLateLoginHandoffStartedAt = Date.now();

  function hkNativeGameLoginReady() {
    // PRELOGIN_ZERO_GAME_API_R1
    // Normal path: the native game itself made an authenticated /player/me and
    // our passive observer captured both the response and its bearer.
    return !!(playerDocument && apiHeaders.Authorization);
  }

  function hkPriorNativePlayerMeEvidence() {
    try {
      const allowedOrigins = new Set([new URL(GAME_API_FALLBACK).origin]);
      if (apiBase) allowedOrigins.add(new URL(apiBase).origin);
      for (const entry of performance.getEntriesByType('resource').slice().reverse()) {
        const url = new URL(String(entry?.name || ''), location.href);
        if (url.pathname === '/player/me' && allowedOrigins.has(url.origin)) return true;
      }
    } catch (_) {}
    return false;
  }

  async function hkTryLateLoginHandoff() {
    if (hkNativeGameLoginReady() || hkLateLoginHandoffBusy) return hkNativeGameLoginReady();
    if (Date.now() < hkLateLoginHandoffNextAt || hkLateLoginHandoffAttempts >= 6) return false;

    restoreGameApiBaseFromPerformance();
    refreshStoredGameAuthorization();
    const token = currentGameBearer();
    const tokenReady = !!token && jwtExpiration(token) > Date.now() + 5000;
    const nativePlayerMeSeen = hkPriorNativePlayerMeEvidence();
    const nativeAuthParams = readNativeGameAuthParams();
    const storageFallbackReady =
      Date.now() - hkLateLoginHandoffStartedAt >= 2500 &&
      !!nativeAuthParams?.authType &&
      !!nativeAuthParams?.authData &&
      tokenReady;

    // We never create a game session here. Late handoff is allowed only after
    // evidence that the native game has already authenticated, then performs
    // one read-only /player/me to recover state missed by a late bookmarklet.
    if (!tokenReady || (!nativePlayerMeSeen && !storageFallbackReady)) return false;

    hkLateLoginHandoffBusy = true;
    hkLateLoginHandoffAttempts += 1;
    hkLateLoginHandoffNextAt = Date.now() + 1500;
    hkStartupStage = 'LATE_HANDOFF';
    recordDiagnostic('late-login-handoff-attempt', {
      revision:HK_LATE_LOGIN_HANDOFF_REV,
      attempt:hkLateLoginHandoffAttempts,
      nativePlayerMeSeen,
      authSource:nativeAuthParams?.source || '',
      tokenFingerprint:diagnosticFingerprint(token),
    });
    try {
      const ok = await bootstrapLateGameConnection();
      recordDiagnostic('late-login-handoff-result', {ok, attempt:hkLateLoginHandoffAttempts});
      return !!ok && hkNativeGameLoginReady();
    } finally {
      hkLateLoginHandoffBusy = false;
      if (!hkNativeGameLoginReady()) hkStartupStage = 'WAIT_NATIVE_LOGIN';
    }
  }

  async function startAfterNativeGameLogin() {
    if (hkNativeLoginRuntimeStarted) return;
    if (!hkNativeGameLoginReady()) {
      hkStartupStage = 'WAIT_NATIVE_LOGIN';
      try {
        if (await hkTryLateLoginHandoff()) {
          setTimeout(startAfterNativeGameLogin, 0);
          return;
        }
      } catch (error) {
        recordDiagnostic('late-login-handoff-error',{error:error?.message || error});
      }
      setTimeout(startAfterNativeGameLogin, 500);
      return;
    }
    hkNativeLoginRuntimeStarted = true;
"""
if old not in s:
    raise SystemExit("native login gate block not found")
s = s.replace(old, new, 1)

s = s.replace(
    "    hkStartupStage === 'RENDER'\n  );",
    "    hkStartupStage === 'RENDER' ||\n    hkStartupStage === 'WAIT_NATIVE_LOGIN' ||\n    hkStartupStage === 'LATE_HANDOFF'\n  );",
    1,
)

checks = [
    "// @version      1.17.13",
    "const BUILD_VERSION = '1.17.13';",
    "core-20260921-r15-late-login-handoff",
    "late-login-handoff-20260921-r1",
    "hkPriorNativePlayerMeEvidence()",
    "bootstrapLateGameConnection()",
    "hkStartupStage = 'WAIT_NATIVE_LOGIN';",
    "hkStartupStage = 'LATE_HANDOFF';",
    "AUTH_PASSIVE_SAFETY_R1",
    "TECHNICAL_PASSIVE_AUTH_BRIDGE_R1",
    "maps-shared-runtime-20260921-r7-safe5",
    "explore-e3-single-20260920-r9-runner",
    "const HK_MAP_READ_CONCURRENCY = 5;",
]
for marker in checks:
    if marker not in s:
        raise SystemExit(f"post-patch marker missing: {marker}")

# Safety: the only createFreshGameAuthorization implementation must remain the
# passive blocked one. Do not reintroduce a userscript-owned /auth/create call.
block_start = s.index("async function createFreshGameAuthorization")
block_end = s.index("async function ensureGameAuthorization", block_start)
block = s[block_start:block_end]
if "return '';" not in block or "auth-create-blocked-passive-only" not in block:
    raise SystemExit("passive auth-create safety changed")

PATH.write_text(s, encoding="utf-8")
print("LATE_LOGIN_HANDOFF_PATCH=PASS")
