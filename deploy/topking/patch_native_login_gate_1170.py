from pathlib import Path

TARGET = Path("/tmp/HamsterKingMobile.user.js")
REV = "login-gate-20260920-r1"
MARKER = f"// HK_NATIVE_LOGIN_GATE_V1 {REV}"

def require(text, needle, label):
    if needle not in text:
        raise SystemExit(f"login gate check failed: {label}")

def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"login gate anchor missing: {label}")
    return text.replace(old, new, 1)

def apply_login_gate(text):
    require(text, "// @version      1.17.0", "live 1.17.0")
    require(text, "function currentGameBearer()", "current game bearer helper")
    require(text, "function bootstrapLateGameConnection()", "late bootstrap")
    require(text, "function startNetworkCapture()", "network capture")
    require(text, "function startInterface()", "interface bootstrap")

    text = replace_once(
        text,
        "  showBootstrap();",
        "  // HK UI is intentionally deferred until the native game login has completed.",
        "defer bootstrap bubble",
    )

    old = """  startNetworkCapture();
  startInterface();
  setTimeout(() => bootstrapLateGameConnection(), 250);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', startInterface, {once:true});
  setInterval(() => { ensureGameAuthorization(false, 'background').catch(error => recordDiagnostic('auth-background-error',{error:error?.message || error})); }, 30000);
  setInterval(captureActiveEventCode, 1500);
  setTimeout(() => hkGameBridge.discover(false), 1500);
  setInterval(() => { if (!hkGameBridge.ready) hkGameBridge.discover(false); }, 30000);
  setInterval(() => { if (playerDocument) checkLicense(playerDocument.player || {}, true); }, LICENSE_RECHECK_MS);
  setInterval(() => collectPublicSnapshot(), PUBLIC_SNAPSHOT_INTERVAL_MS);"""

    new = """  let hkNativeLoginRuntimeStarted = false;

  function hkNativeGameLoginReady() {
    if (playerDocument && apiHeaders.Authorization) return true;
    try {
      for (const storage of [sessionStorage, localStorage]) {
        const token = String(storage.getItem('token') || '').trim();
        if (token && jwtExpiration(token) > Date.now() + 5000 && gameBearerPlayerId(token)) return true;
      }
    } catch (_) {}
    try {
      const licenseOrigin = new URL(LICENSE_URL).origin;
      for (const entry of performance.getEntriesByType('resource').slice().reverse()) {
        const url = new URL(String(entry?.name || ''), location.href);
        if (url.origin === licenseOrigin) continue;
        if (url.pathname === '/player/me') return true;
      }
    } catch (_) {}
    return false;
  }

  function startAfterNativeGameLogin() {
    if (hkNativeLoginRuntimeStarted) return;
    if (!hkNativeGameLoginReady()) {
      setTimeout(startAfterNativeGameLogin, 500);
      return;
    }
    hkNativeLoginRuntimeStarted = true;
    showBootstrap();
    startNetworkCapture();
    startInterface();
    setTimeout(() => bootstrapLateGameConnection(), 100);
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', startInterface, {once:true});
    setInterval(() => { ensureGameAuthorization(false, 'background').catch(error => recordDiagnostic('auth-background-error',{error:error?.message || error})); }, 30000);
    setInterval(captureActiveEventCode, 1500);
    setTimeout(() => hkGameBridge.discover(false), 1500);
    setInterval(() => { if (!hkGameBridge.ready) hkGameBridge.discover(false); }, 30000);
    setInterval(() => { if (playerDocument) checkLicense(playerDocument.player || {}, true); }, LICENSE_RECHECK_MS);
    setInterval(() => collectPublicSnapshot(), PUBLIC_SNAPSHOT_INTERVAL_MS);
    recordDiagnostic('native-login-gate-open',{revision:'login-gate-20260920-r1'});
  }

  startAfterNativeGameLogin();"""

    text = replace_once(text, old, new, "defer runtime until native login")

    if MARKER not in text:
        anchor = "  let hkNativeLoginRuntimeStarted = false;"
        require(text, anchor, "login gate marker anchor")
        text = text.replace(anchor, f"  {MARKER}\n{anchor}", 1)

    checks = [
        MARKER,
        "function hkNativeGameLoginReady()",
        "function startAfterNativeGameLogin()",
        "url.pathname === '/player/me'",
        "storage.getItem('token')",
        "startAfterNativeGameLogin();",
        "showBootstrap();",
    ]
    for needle in checks:
        require(text, needle, needle)

    # There must be no unconditional startup of the HK UI before the gate.
    tail = text[text.find(MARKER):]
    if "startAfterNativeGameLogin();" not in tail:
        raise SystemExit("native login gate call missing")

    return text

if __name__ == "__main__":
    source = TARGET.read_text(encoding="utf-8")
    TARGET.write_text(apply_login_gate(source), encoding="utf-8")
    print("HK_NATIVE_LOGIN_GATE_OK")
