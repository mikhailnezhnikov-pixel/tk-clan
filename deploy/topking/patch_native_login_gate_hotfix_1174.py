from pathlib import Path

TARGET = Path('/tmp/HamsterKingMobile.user.js')
REV = 'login-gate-hotfix-20260920-r2'
MARKER = f"HK_NATIVE_LOGIN_GATE_REV = '{REV}'"

def require(text, needle, label):
    if needle not in text:
        raise SystemExit(f'login gate hotfix check failed: {label}')

def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f'login gate hotfix anchor missing: {label}')
    return text.replace(old, new, 1)

def apply_hotfix(text):
    s = text
    require(s, '// @version      1.17.4', 'live 1.17.4')
    require(s, "HK_LAUNCHER_REV = 'launcher-hotfix-20260920-r1'", 'launcher hotfix r1')
    require(s, '// HK_NATIVE_LOGIN_GATE_V1 login-gate-20260920-r1', 'native login gate r1')
    require(s, 'function hkNativeGameLoginReady()', 'native login gate function')

    if MARKER in s:
        return validate(s)

    s = replace_once(
        s,
        "  let hkNativeLoginRuntimeStarted = false;",
        "  const " + MARKER + ";\n  let hkNativeLoginRuntimeStarted = false;",
        'gate hotfix marker',
    )

    old = """    } catch (_) {}
    return false;
  }

  function startAfterNativeGameLogin() {"""

    new = """    } catch (_) {}

    // The current game city is rendered with Leaflet/OpenStreetMap.  A visible
    // native map is a strong signal that the player is already inside the game,
    // even when the game no longer exposes its bearer token under the old
    // localStorage key expected by the original gate.
    try {
      const nativeMap = document.querySelector('.leaflet-container, .leaflet-map-pane, .leaflet-control-container');
      if (nativeMap && (nativeMap.offsetWidth || nativeMap.offsetHeight || nativeMap.getClientRects().length)) return true;
      const osm = document.querySelector('a[href*="openstreetmap.org"]');
      if (osm && (osm.offsetWidth || osm.offsetHeight || osm.getClientRects().length)) return true;
    } catch (_) {}

    // Also accept observed authenticated game traffic.  The API has changed
    // route/storage details over time, so do not depend on /player/me alone.
    try {
      const licenseOrigin = new URL(LICENSE_URL).origin;
      for (const entry of performance.getEntriesByType('resource').slice().reverse()) {
        const url = new URL(String(entry?.name || ''), location.href);
        if (url.origin === licenseOrigin) continue;
        if (!/(^|\\.)hwgame\\.cloud$/i.test(url.hostname)) continue;
        if (/\\/(player|city|shop|clan|alliance|war|wars|building|business|fair|game_area)(?:\\/|$)/i.test(url.pathname)) return true;
      }
    } catch (_) {}

    return false;
  }

  function startAfterNativeGameLogin() {"""

    s = replace_once(s, old, new, 'recognize loaded native game shell')
    return validate(s)

def validate(s):
    checks = [
        '// @version      1.17.4',
        "HK_LAUNCHER_REV = 'launcher-hotfix-20260920-r1'",
        '// HK_NATIVE_LOGIN_GATE_V1 login-gate-20260920-r1',
        MARKER,
        "document.querySelector('.leaflet-container, .leaflet-map-pane, .leaflet-control-container')",
        "a[href*=\"openstreetmap.org\"]",
        "hwgame\\.cloud",
        "game_area",
        'function startAfterNativeGameLogin()',
    ]
    for needle in checks:
        require(s, needle, needle)
    return s

if __name__ == '__main__':
    source = TARGET.read_text(encoding='utf-8')
    TARGET.write_text(apply_hotfix(source), encoding='utf-8')
    print('HK_NATIVE_LOGIN_GATE_HOTFIX_1174_OK')
