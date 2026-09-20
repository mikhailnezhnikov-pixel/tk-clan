from pathlib import Path

TARGET = Path('/tmp/HamsterKingMobile.user.js')
REV = 'core-20260920-r6'
MARKER = f"HK_CORE_REVISION = '{REV}'"

def require(text, needle, label):
    if needle not in text:
        raise SystemExit(f'core r6 check failed: {label}')

def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f'core r6 anchor missing: {label}')
    return text.replace(old, new, 1)

def apply(text):
    s=text
    require(s, '// @version      1.17.4', 'live version')
    require(s, "HK_RUNTIME_TAKEOVER_REV = 'runtime-takeover-20260920-r5'", 'runtime takeover r5')
    require(s, "HK_LAUNCHER_HANDOFF_REV = 'launcher-handoff-20260920-r4'", 'launcher handoff r4')
    if MARKER in s:
        return validate(s)

    s=replace_once(
        s,
        "  const HK_RUNTIME_TAKEOVER_REV = 'runtime-takeover-20260920-r5';",
        "  const HK_RUNTIME_TAKEOVER_REV = 'runtime-takeover-20260920-r5';\n  const HK_CORE_REVISION = 'core-20260920-r6';",
        'core revision marker',
    )

    s=replace_once(
        s,
        "  if (previousRuntime?.active && hkRuntimeAtLeast(previousRuntime.version, BUILD_VERSION)) {\n    try { previousRuntime.open?.(); } catch (_) {}\n    return;\n  }",
        "  if (previousRuntime?.active && previousRuntime.revision === HK_CORE_REVISION) {\n    try { previousRuntime.open?.(); } catch (_) {}\n    return;\n  }",
        'revision-aware runtime guard',
    )

    s=replace_once(
        s,
        "  const runtime = {active:true, version:BUILD_VERSION, open:null};\n  window.__HK_MOBILE_RUNTIME__ = runtime;\n  window.__HK_MOBILE_LOADED__ = true;\n  window.__HK_MOBILE_VERSION__ = BUILD_VERSION;",
        "  const runtime = {active:true, version:BUILD_VERSION, revision:HK_CORE_REVISION, open:null, ensure:null, destroy:null};\n  window.__HK_MOBILE_RUNTIME__ = runtime;\n  window.__HK_MOBILE_LOADED__ = true;\n  window.__HK_MOBILE_VERSION__ = BUILD_VERSION;\n  window.__HK_MOBILE_REVISION__ = HK_CORE_REVISION;",
        'revision on runtime',
    )

    s=replace_once(
        s,
        "      bootstrapButton = document.createElement('button');\n      bootstrapButton.type = 'button';",
        "      bootstrapButton = document.createElement('button');\n      bootstrapButton.id = 'hk-bootstrap-button';\n      bootstrapButton.dataset.hkRevision = HK_CORE_REVISION;\n      bootstrapButton.type = 'button';",
        'bootstrap ownership',
    )

    s=replace_once(
        s,
        "    root = document.createElement('div'); root.id = 'hk-mobile-root';",
        "    root = document.createElement('div'); root.id = 'hk-mobile-root'; root.dataset.hkRevision = HK_CORE_REVISION;",
        'root ownership',
    )

    old_runtime_open = """    runtime.open = () => {
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
    };"""

    new_runtime_open = """    runtime.ensure = () => {
      try {
        if (!root?.isConnected || root.dataset.hkRevision !== HK_CORE_REVISION || !root.querySelector('#hk-fab')) {
          try { root?.remove(); } catch (_) {}
          root = null;
          panel = null;
          startInterface();
        }
        if (root?.isConnected && root.dataset.hkRevision === HK_CORE_REVISION && root.querySelector('#hk-fab')) {
          hideBootstrap();
          return true;
        }
      } catch (_) {}
      return false;
    };
    runtime.open = () => {
      try {
        runtime.ensure?.();
        if (panel?.isConnected) {
          panel.classList.add('open');
          updateWatermark();
        } else {
          showBootstrap();
        }
      } catch (error) {
        showBootstrap(error?.message || either('Не удалось восстановить HK','Could not restore HK'));
      }
    };"""

    s=replace_once(s, old_runtime_open, new_runtime_open, 'runtime ensure')

    old_tail = """  startInterface();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startInterface, {once:true});
  }
  startAfterNativeGameLogin();
})();"""

    new_tail = """  runtime.destroy = () => {
    runtime.active = false;
    try { root?.remove(); } catch (_) {}
    try { bootstrapButton?.remove(); } catch (_) {}
    root = null;
    panel = null;
  };

  startInterface();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startInterface, {once:true});
  }
  startAfterNativeGameLogin();
  setInterval(() => {
    if (runtime.active) runtime.ensure?.();
  }, 1000);
})();"""

    s=replace_once(s, old_tail, new_tail, 'runtime watchdog')

    return validate(s)

def validate(s):
    checks=[
        "// @version      1.17.4",
        MARKER,
        "previousRuntime?.active && previousRuntime.revision === HK_CORE_REVISION",
        "revision:HK_CORE_REVISION",
        "window.__HK_MOBILE_REVISION__ = HK_CORE_REVISION",
        "bootstrapButton.id = 'hk-bootstrap-button'",
        "root.dataset.hkRevision = HK_CORE_REVISION",
        "runtime.ensure = () =>",
        "runtime.destroy = () =>",
        "if (runtime.active) runtime.ensure?.();",
        "HK_RUNTIME_TAKEOVER_REV = 'runtime-takeover-20260920-r5'",
    ]
    for needle in checks:
        require(s, needle, needle)
    return s

if __name__ == '__main__':
    source=TARGET.read_text(encoding='utf-8')
    TARGET.write_text(apply(source),encoding='utf-8')
    print('HK_CORE_R6_OK')
