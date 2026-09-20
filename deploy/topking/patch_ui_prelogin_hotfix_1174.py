from pathlib import Path

TARGET = Path('/tmp/HamsterKingMobile.user.js')
REV = 'ui-prelogin-20260920-r3'
MARKER = f"HK_UI_PRELOGIN_REV = '{REV}'"

def require(text, needle, label):
    if needle not in text:
        raise SystemExit(f'ui prelogin hotfix check failed: {label}')

def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f'ui prelogin hotfix anchor missing: {label}')
    return text.replace(old, new, 1)

def apply_hotfix(text):
    s = text
    require(s, '// @version      1.17.4', 'live 1.17.4')
    require(s, "HK_LAUNCHER_REV = 'launcher-hotfix-20260920-r1'", 'launcher hotfix r1')
    require(s, "HK_NATIVE_LOGIN_GATE_REV = 'login-gate-hotfix-20260920-r2'", 'login gate r2')
    require(s, 'function startAfterNativeGameLogin()', 'native login gate')

    if MARKER in s:
        return validate(s)

    s = replace_once(
        s,
        "  const HK_NATIVE_LOGIN_GATE_REV = 'login-gate-hotfix-20260920-r2';",
        "  const HK_NATIVE_LOGIN_GATE_REV = 'login-gate-hotfix-20260920-r2';\n  const " + MARKER + ";",
        'ui-prelogin marker',
    )

    # The UI must not depend on game auth. Mount the launcher/panel as soon as
    # the document body exists; the native-login gate remains responsible only
    # for starting authenticated/network work.
    old = """  startAfterNativeGameLogin();"""
    new = """  startInterface();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startInterface, {once:true});
  }
  startAfterNativeGameLogin();"""
    s = replace_once(s, old, new, 'mount UI before native-login gate')

    return validate(s)

def validate(s):
    checks = [
        '// @version      1.17.4',
        "HK_LAUNCHER_REV = 'launcher-hotfix-20260920-r1'",
        "HK_NATIVE_LOGIN_GATE_REV = 'login-gate-hotfix-20260920-r2'",
        MARKER,
        "  startInterface();\n  if (document.readyState === 'loading') {\n    document.addEventListener('DOMContentLoaded', startInterface, {once:true});\n  }\n  startAfterNativeGameLogin();",
    ]
    for needle in checks:
        require(s, needle, needle)

    ui_pos = s.rfind("  startInterface();\n  if (document.readyState === 'loading')")
    gate_pos = s.rfind('  startAfterNativeGameLogin();')
    if ui_pos < 0 or gate_pos < 0 or ui_pos >= gate_pos:
        raise SystemExit('ui prelogin validation failed: UI must start before gate')
    return s

if __name__ == '__main__':
    source = TARGET.read_text(encoding='utf-8')
    TARGET.write_text(apply_hotfix(source), encoding='utf-8')
    print('HK_UI_PRELOGIN_HOTFIX_1174_OK')
