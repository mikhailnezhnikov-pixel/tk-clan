from pathlib import Path

TARGET = Path('/tmp/HamsterKingMobile.user.js')
REV = 'launcher-hotfix-20260920-r1'
MARKER = f"HK_LAUNCHER_REV = '{REV}'"

def require(text, needle, label):
    if needle not in text:
        raise SystemExit(f'launcher hotfix check failed: {label}')

def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f'launcher hotfix anchor missing: {label}')
    return text.replace(old, new, 1)

def apply_hotfix(text):
    s = text
    require(s, '// @version      1.17.4', 'live 1.17.4')
    require(s, "HK_AUTO_ROUTINES_REV = 'auto-routines-20260920-r1'", 'Auto Routines 1.17.4 marker')
    require(s, '// HK_NATIVE_LOGIN_GATE_V1 login-gate-20260920-r1', 'native login gate marker')

    if MARKER in s:
        return validate(s)

    # Keep a visible HK launcher while the native-login gate waits.
    s = replace_once(
        s,
        "bootstrapProblem = String(problem || bootstrapProblem || 'Панель не смогла запуститься.');",
        "bootstrapProblem = String(problem || bootstrapProblem || 'Ожидаю вход в игру…');",
        'bootstrap waiting message',
    )
    s = replace_once(
        s,
        "  function hideBootstrap() { bootstrapButton?.remove(); }\n  // HK UI is intentionally deferred until the native game login has completed.",
        "  function hideBootstrap() { bootstrapButton?.remove(); }\n  showBootstrap();\n  // HK UI is intentionally deferred until the native game login has completed.",
        'keep bootstrap visible through native-login wait',
    )

    # Marker without consuming the 1.17.5 feature version.
    s = replace_once(
        s,
        "  const VERSION = BUILD_VERSION;",
        "  const VERSION = BUILD_VERSION;\n  const " + MARKER + ";",
        'launcher marker',
    )

    # A stale detached root must not permanently block remounting.
    s = replace_once(
        s,
        "  function renderUI() {\n    if (!document.body || root) return;",
        "  function renderUI() {\n    if (!document.body) return;\n    if (root?.isConnected && root.querySelector('#hk-fab')) return;\n    if (root && !root.isConnected) { root = null; panel = null; }",
        'stale root recovery',
    )

    # Keep game/global styles from hiding the launcher.
    s = replace_once(
        s,
        "#hk-fab{width:58px;height:58px;border:0;border-radius:50%;",
        "#hk-fab{display:block!important;visibility:visible!important;opacity:1!important;width:58px;height:58px;border:0;border-radius:50%;",
        'fab visibility hardening',
    )

    # Do not remove the fallback until the permanent FAB is confirmed mounted.
    s = replace_once(
        s,
        "    document.body.appendChild(root);\n    hideBootstrap();\n    panel = root.querySelector('#hk-panel');",
        "    document.body.appendChild(root);\n    panel = root.querySelector('#hk-panel');",
        'delay bootstrap removal',
    )
    s = replace_once(
        s,
        "    installFabDragging(root.querySelector('#hk-fab'));\n    root.querySelector('.hk-close').onclick = () => panel.classList.remove('open');",
        """    const permanentFab = root.querySelector('#hk-fab');
    if (!permanentFab?.isConnected) {
      showBootstrap(either('Кнопка HK не смонтирована','HK launcher was not mounted'));
      throw new Error('hk-fab-not-mounted');
    }
    installFabDragging(permanentFab);
    hideBootstrap();
    root.querySelector('.hk-close').onclick = () => panel.classList.remove('open');""",
        'verify permanent fab before hiding fallback',
    )

    # Re-running the loader should recover a detached launcher instead of
    # opening a panel that is no longer attached to the document.
    s = replace_once(
        s,
        "    runtime.open = () => { try { panel?.classList.add('open'); updateWatermark(); } catch (_) {} };",
        """    runtime.open = () => {
      try {
        if (!root?.isConnected || !root.querySelector('#hk-fab')) {
          root = null;
          panel = null;
          startInterface();
        }
        if (panel?.isConnected) {
          panel.classList.add('open');
          updateWatermark();
        } else {
          showBootstrap();
        }
      } catch (error) {
        showBootstrap(error?.message || either('Не удалось восстановить HK','Could not restore HK'));
      }
    };""",
        'runtime launcher recovery',
    )

    return validate(s)

def validate(s):
    checks = [
        '// @version      1.17.4',
        MARKER,
        "showBootstrap();\n  // HK UI is intentionally deferred",
        "if (root?.isConnected && root.querySelector('#hk-fab')) return;",
        "if (root && !root.isConnected) { root = null; panel = null; }",
        "#hk-fab{display:block!important;visibility:visible!important;opacity:1!important;",
        "const permanentFab = root.querySelector('#hk-fab');",
        "if (!permanentFab?.isConnected)",
        "installFabDragging(permanentFab);",
        "hideBootstrap();",
        "if (!root?.isConnected || !root.querySelector('#hk-fab'))",
        "startInterface();",
        "panel?.isConnected",
        "HK_AUTO_ROUTINES_REV = 'auto-routines-20260920-r1'",
        "// HK_NATIVE_LOGIN_GATE_V1 login-gate-20260920-r1",
    ]
    for needle in checks:
        require(s, needle, needle)

    # hideBootstrap must now occur after installFabDragging(permanentFab).
    append_pos = s.find('    document.body.appendChild(root);')
    install_pos = s.find('    installFabDragging(permanentFab);', append_pos)
    hide_pos = s.find('    hideBootstrap();', append_pos)
    if min(append_pos, install_pos, hide_pos) < 0 or not (append_pos < install_pos < hide_pos):
        raise SystemExit('launcher hotfix validation failed: fallback removal order')

    return s

if __name__ == '__main__':
    source = TARGET.read_text(encoding='utf-8')
    TARGET.write_text(apply_hotfix(source), encoding='utf-8')
    print('HK_LAUNCHER_HOTFIX_1174_OK')
