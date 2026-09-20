from pathlib import Path

TARGET = Path('/tmp/HamsterKingMobile.user.js')
REV = 'launcher-handoff-20260920-r4'
MARKER = f"HK_LAUNCHER_HANDOFF_REV = '{REV}'"

def require(text, needle, label):
    if needle not in text:
        raise SystemExit(f'launcher handoff hotfix check failed: {label}')

def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f'launcher handoff hotfix anchor missing: {label}')
    return text.replace(old, new, 1)

def apply_hotfix(text):
    s = text
    require(s, '// @version      1.17.4', 'live 1.17.4')
    require(s, "HK_LAUNCHER_REV = 'launcher-hotfix-20260920-r1'", 'launcher r1')
    require(s, "HK_NATIVE_LOGIN_GATE_REV = 'login-gate-hotfix-20260920-r2'", 'gate r2')
    require(s, "HK_UI_PRELOGIN_REV = 'ui-prelogin-20260920-r3'", 'ui prelogin r3')

    if MARKER in s:
        return validate(s)

    s = replace_once(
        s,
        "  const HK_UI_PRELOGIN_REV = 'ui-prelogin-20260920-r3';",
        "  const HK_UI_PRELOGIN_REV = 'ui-prelogin-20260920-r3';\n  const " + MARKER + ";",
        'handoff marker',
    )

    # startInterface must only consider a fully mounted permanent launcher as
    # "already started". A stale/partial root must be discarded and remounted.
    old_start = """  function startInterface() {
    if (root) return;
    try {
      if (document.body) renderUI();
    } catch (error) {
      showBootstrap(error?.message || error);
      return;
    }
    if (!root) setTimeout(startInterface, 250);
  }"""

    new_start = """  function startInterface() {
    if (root?.isConnected && root.querySelector('#hk-fab')) {
      hideBootstrap();
      return;
    }
    if (root) {
      try { root.remove(); } catch (_) {}
      root = null;
      panel = null;
    }
    try {
      if (document.body) renderUI();
    } catch (error) {
      try { root?.remove(); } catch (_) {}
      root = null;
      panel = null;
      showBootstrap(error?.message || error);
      setTimeout(startInterface, 500);
      return;
    }
    if (!root?.isConnected || !root.querySelector('#hk-fab')) setTimeout(startInterface, 250);
  }"""

    s = replace_once(s, old_start, new_start, 'self-healing startInterface')

    # Once the game-login gate opens, never resurrect the temporary HK…
    # button over an already mounted permanent launcher.
    old_gate = """    hkNativeLoginRuntimeStarted = true;
    showBootstrap();
    startNetworkCapture();
    startInterface();"""

    new_gate = """    hkNativeLoginRuntimeStarted = true;
    if (!root?.isConnected || !root.querySelector('#hk-fab')) showBootstrap();
    startNetworkCapture();
    startInterface();"""

    s = replace_once(s, old_gate, new_gate, 'do not resurrect bootstrap over permanent launcher')

    return validate(s)

def validate(s):
    checks = [
        '// @version      1.17.4',
        "HK_LAUNCHER_REV = 'launcher-hotfix-20260920-r1'",
        "HK_NATIVE_LOGIN_GATE_REV = 'login-gate-hotfix-20260920-r2'",
        "HK_UI_PRELOGIN_REV = 'ui-prelogin-20260920-r3'",
        MARKER,
        "if (root?.isConnected && root.querySelector('#hk-fab')) {",
        "hideBootstrap();",
        "root = null;\n      panel = null;",
        "setTimeout(startInterface, 500);",
        "if (!root?.isConnected || !root.querySelector('#hk-fab')) showBootstrap();",
    ]
    for needle in checks:
        require(s, needle, needle)

    # Ensure the gate no longer contains unconditional showBootstrap followed
    # by startNetworkCapture.
    gate = s[s.find('function startAfterNativeGameLogin()'):]
    if "hkNativeLoginRuntimeStarted = true;\n    showBootstrap();\n    startNetworkCapture();" in gate:
        raise SystemExit('launcher handoff validation failed: unconditional bootstrap resurrection remains')
    return s

if __name__ == '__main__':
    source = TARGET.read_text(encoding='utf-8')
    TARGET.write_text(apply_hotfix(source), encoding='utf-8')
    print('HK_LAUNCHER_HANDOFF_HOTFIX_1174_OK')
