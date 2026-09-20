from pathlib import Path

TARGET = Path('/tmp/HamsterKingMobile.user.js')
REV = 'runtime-takeover-20260920-r5'
MARKER = f"HK_RUNTIME_TAKEOVER_REV = '{REV}'"

def require(text, needle, label):
    if needle not in text:
        raise SystemExit(f'runtime takeover hotfix check failed: {label}')

def apply_hotfix(text):
    s=text
    require(s, '// @version      1.17.4', 'live 1.17.4')
    require(s, "HK_LAUNCHER_HANDOFF_REV = 'launcher-handoff-20260920-r4'", 'handoff r4')
    if MARKER in s:
        return validate(s)

    old="""  const BUILD_VERSION = typeof GM_info !== 'undefined' && GM_info?.script?.version
    ? String(GM_info.script.version)
    : '1.17.4';
  const previousRuntime = window.__HK_MOBILE_RUNTIME__;
  if (previousRuntime?.active) {
    try { previousRuntime.open?.(); } catch (_) {}
    return;
  }
  const runtime = {active:true, version:BUILD_VERSION, open:null};"""

    new="""  const BUILD_VERSION = '1.17.4';
  const HK_RUNTIME_TAKEOVER_REV = 'runtime-takeover-20260920-r5';
  function hkRuntimeVersionTuple(value) {
    const match = String(value || '').match(/^\\s*(\\d+(?:\\.\\d+)*)/);
    return match ? match[1].split('.').map(Number) : [];
  }
  function hkRuntimeAtLeast(value, minimum) {
    const current = hkRuntimeVersionTuple(value);
    const required = hkRuntimeVersionTuple(minimum);
    if (!current.length || !required.length) return false;
    const width = Math.max(current.length, required.length);
    while (current.length < width) current.push(0);
    while (required.length < width) required.push(0);
    for (let index = 0; index < width; index++) {
      if (current[index] !== required[index]) return current[index] > required[index];
    }
    return true;
  }
  const previousRuntime = window.__HK_MOBILE_RUNTIME__;
  if (previousRuntime?.active && hkRuntimeAtLeast(previousRuntime.version, BUILD_VERSION)) {
    try { previousRuntime.open?.(); } catch (_) {}
    return;
  }
  if (previousRuntime?.active) {
    try { previousRuntime.active = false; } catch (_) {}
    try { document.getElementById('hk-mobile-root')?.remove(); } catch (_) {}
    try { document.querySelectorAll('#hk-fab').forEach(node => node.remove()); } catch (_) {}
    try { window.__HK_MOBILE_RUNTIME__ = null; } catch (_) {}
    try { window.__HK_MOBILE_LOADED__ = false; } catch (_) {}
  }
  const runtime = {active:true, version:BUILD_VERSION, open:null};"""

    if old not in s:
        raise SystemExit('runtime takeover hotfix anchor missing: bootstrap runtime guard')
    s=s.replace(old,new,1)
    return validate(s)

def validate(s):
    checks=[
        "// @version      1.17.4",
        "const BUILD_VERSION = '1.17.4';",
        MARKER,
        "hkRuntimeAtLeast(previousRuntime.version, BUILD_VERSION)",
        "previousRuntime.active = false",
        "document.getElementById('hk-mobile-root')?.remove()",
        "window.__HK_MOBILE_LOADED__ = false",
    ]
    for needle in checks:
        require(s, needle, needle)
    if "const BUILD_VERSION = typeof GM_info" in s[:3000]:
        raise SystemExit('runtime takeover validation failed: GM_info build version remains')
    return s

if __name__ == '__main__':
    source=TARGET.read_text(encoding='utf-8')
    TARGET.write_text(apply_hotfix(source),encoding='utf-8')
    print('HK_RUNTIME_TAKEOVER_HOTFIX_1174_OK')
