from pathlib import Path

TARGET = Path('/tmp/HamsterKingMobile.user.js')
REV = 'core-20260920-r5'
MARKER = f"HK_CORE_REVISION = '{REV}'"

def require(text, needle, label):
    if needle not in text:
        raise SystemExit(f'core revision hotfix check failed: {label}')

def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f'core revision hotfix anchor missing: {label}')
    return text.replace(old, new, 1)

def apply_hotfix(text):
    s = text
    require(s, '// @version      1.17.4', 'live 1.17.4')
    require(s, "HK_LAUNCHER_HANDOFF_REV = 'launcher-handoff-20260920-r4'", 'launcher handoff r4')

    if MARKER in s:
        return validate(s)

    old_runtime = """  const BUILD_VERSION = typeof GM_info !== 'undefined' && GM_info?.script?.version
    ? String(GM_info.script.version)
    : '1.17.4';
  const previousRuntime = window.__HK_MOBILE_RUNTIME__;
  if (previousRuntime?.active) {
    try { previousRuntime.open?.(); } catch (_) {}
    return;
  }
  const runtime = {active:true, version:BUILD_VERSION, open:null};
  window.__HK_MOBILE_RUNTIME__ = runtime;
  window.__HK_MOBILE_LOADED__ = true;
  window.__HK_MOBILE_VERSION__ = BUILD_VERSION;"""

    new_runtime = """  const BUILD_VERSION = typeof GM_info !== 'undefined' && GM_info?.script?.version
    ? String(GM_info.script.version)
    : '1.17.4';
  const HK_CORE_REVISION = 'core-20260920-r5';
  const previousRuntime = window.__HK_MOBILE_RUNTIME__;
  if (previousRuntime?.active && previousRuntime.revision === HK_CORE_REVISION) {
    try { previousRuntime.open?.(); } catch (_) {}
    return;
  }
  if (previousRuntime?.active) {
    try { previousRuntime.destroy?.(); } catch (_) {}
    try { previousRuntime.active = false; } catch (_) {}
  }
  try {
    document.querySelector('#hk-mobile-root')?.remove();
    document.querySelector('#hk-bootstrap-button')?.remove();
  } catch (_) {}
  const runtime = {active:true, version:BUILD_VERSION, revision:HK_CORE_REVISION, open:null, destroy:null};
  window.__HK_MOBILE_RUNTIME__ = runtime;
  window.__HK_MOBILE_LOADED__ = true;
  window.__HK_MOBILE_VERSION__ = BUILD_VERSION;
  window.__HK_MOBILE_REVISION__ = HK_CORE_REVISION;"""

    s = replace_once(s, old_runtime, new_runtime, 'revision-aware runtime ownership')

    old_bootstrap = """      bootstrapButton = document.createElement('button');
      bootstrapButton.type = 'button';"""
    new_bootstrap = """      bootstrapButton = document.createElement('button');
      bootstrapButton.id = 'hk-bootstrap-button';
      bootstrapButton.dataset.hkRevision = HK_CORE_REVISION;
      bootstrapButton.type = 'button';"""
    s = replace_once(s, old_bootstrap, new_bootstrap, 'bootstrap ownership id')

    old_root = """    root = document.createElement('div'); root.id = 'hk-mobile-root';"""
    new_root = """    root = document.createElement('div'); root.id = 'hk-mobile-root'; root.dataset.hkRevision = HK_CORE_REVISION;"""
    s = replace_once(s, old_root, new_root, 'root ownership revision')

    old_tail = """  startInterface();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startInterface, {once:true});
  }
  startAfterNativeGameLogin();
})();"""

    new_tail = """  function purgeLegacyBootstrap() {
    if (!root?.isConnected || !root.querySelector('#hk-fab')) return;
    try {
      document.querySelectorAll('button').forEach(button => {
        if (button === root.querySelector('#hk-fab') || button.id === 'hk-bootstrap-button') return;
        const label = String(button.textContent || '').trim();
        const inline = String(button.getAttribute('style') || '');
        if (/^HK(?:…|\.\.\.|!)?$/.test(label) && inline.includes('position:fixed') && inline.includes('width:58px') && inline.includes('height:58px')) {
          button.remove();
        }
      });
    } catch (_) {}
  }

  runtime.destroy = () => {
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
    if (!runtime.active) return;
    if (!root?.isConnected || root.dataset.hkRevision !== HK_CORE_REVISION || !root.querySelector('#hk-fab')) {
      startInterface();
      return;
    }
    hideBootstrap();
    purgeLegacyBootstrap();
  }, 1000);
})();"""

    s = replace_once(s, old_tail, new_tail, 'runtime ownership watchdog')
    return validate(s)

def validate(s):
    checks = [
        '// @version      1.17.4',
        MARKER,
        "previousRuntime?.active && previousRuntime.revision === HK_CORE_REVISION",
        "revision:HK_CORE_REVISION",
        "window.__HK_MOBILE_REVISION__ = HK_CORE_REVISION",
        "bootstrapButton.id = 'hk-bootstrap-button'",
        "root.dataset.hkRevision = HK_CORE_REVISION",
        "function purgeLegacyBootstrap()",
        "runtime.destroy = () =>",
        "root.dataset.hkRevision !== HK_CORE_REVISION",
        "setInterval(() =>",
        "HK_LAUNCHER_HANDOFF_REV = 'launcher-handoff-20260920-r4'",
    ]
    for needle in checks:
        require(s, needle, needle)
    return s

if __name__ == '__main__':
    source = TARGET.read_text(encoding='utf-8')
    TARGET.write_text(apply_hotfix(source), encoding='utf-8')
    print('HK_CORE_REVISION_HOTFIX_1174_OK')
