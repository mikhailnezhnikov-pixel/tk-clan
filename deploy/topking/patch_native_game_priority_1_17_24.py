from pathlib import Path

PATH = Path("/tmp/HamsterKingMobile.user.js")
s = PATH.read_text(encoding="utf-8")

def require(marker, label=None):
    if marker not in s:
        raise SystemExit("missing expected marker: " + (label or marker[:180]))

def replace_once(old, new, label):
    global s
    count=s.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 match, got {count}")
    s=s.replace(old,new,1)

for marker in [
    "// @version      1.17.24",
    "const BUILD_VERSION = '1.17.24';",
    "const HK_CORE_REVISION = 'core-20260921-r27-businesses-runner-canon';",
    "puzzle-solver-v3-embedded-20260921-r1",
    "function installNetworkCapture()",
    "hkGameBridge.noteMutation(path, method);",
]:
    require(marker)

release = "// @release-note Встроен фоновый HK Puzzle Solver v3: автоматически показывает порядок нажатий для Lights Out 3×3 и Battle."
replace_once(
    release,
    "// @release-note Исправлена совместимость с обычной игрой: HK больше не запускает дополнительное обновление player state после нативных действий пользователя.\n" + release,
    "release note"
)

# Critical fix: passive interception must stay passive. The native game already
# updates its own React state after its requests. Marking native requests dirty
# scheduled an extra bridge refresh ~180 ms later, racing the server's player
# lock and producing HTTP 429 "Player state is locked by other request".
replace_once(
    """      if (hkNativeLoginRuntimeStarted && response.ok && isGameApiRequest(url)) hkGameBridge.noteMutation(path, init?.method || input?.method || 'GET');
      if(response.ok && isGameApiRequest(url) && path!=='/player/me') response.clone().json().then(body=>acceptSharedGameResponse(url,body)).catch(()=>{});""",
    """      // Native game traffic is observation-only. Never schedule HK's React
      // refresh bridge from the game's own request; doing so creates a second
      // player-state request while the server may still hold its lock.
      if(response.ok && isGameApiRequest(url) && path!=='/player/me') response.clone().json().then(body=>acceptSharedGameResponse(url,body)).catch(()=>{});""",
    "fetch native bridge side effect"
)

replace_once(
    """              if (hkNativeLoginRuntimeStarted) hkGameBridge.noteMutation(path, this.__hkMethod || 'GET');
              if(path!=='/player/me')acceptSharedGameResponse(this.__hkUrl,body);""",
    """              // XHR from the native game is passive input for HK only.
              // Do not trigger an HK-side player refresh after native mutations.
              if(path!=='/player/me')acceptSharedGameResponse(this.__hkUrl,body);""",
    "xhr native bridge side effect"
)

# Marker for audits and future regressions.
anchor = "  function installNetworkCapture() {"
replace_once(
    anchor,
    "  const HK_NATIVE_GAME_PRIORITY_REV = 'native-game-priority-no-bridge-race-20260921-r1';\n\n" + anchor,
    "native game priority marker"
)

for marker in [
    "const HK_NATIVE_GAME_PRIORITY_REV = 'native-game-priority-no-bridge-race-20260921-r1';",
    "Native game traffic is observation-only.",
    "XHR from the native game is passive input for HK only.",
    "hkGameBridge.noteMutation(path, method);",
    "puzzle-solver-v3-embedded-20260921-r1",
    "businesses-finalize-single-snapshot-20260921-r1",
]:
    require(marker,"post-patch "+marker)

network = s[s.index("  function installNetworkCapture()"):s.index("  function pitState()", s.index("  function installNetworkCapture()"))]
if "hkGameBridge.noteMutation(" in network:
    raise SystemExit("native network capture still schedules bridge mutation refresh")

PATH.write_text(s,encoding="utf-8")
print("NATIVE_GAME_PRIORITY_NO_BRIDGE_RACE_R1=PASS")
