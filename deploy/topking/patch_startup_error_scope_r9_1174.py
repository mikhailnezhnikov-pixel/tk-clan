from pathlib import Path

path = Path("/tmp/HamsterKingMobile.user.js")
text = path.read_text(encoding="utf-8")

expected_sha_marker = "const HK_STARTUP_ERROR_TRAP_REV = 'startup-error-trap-20260920-r8';"
new_marker = "const HK_STARTUP_ERROR_SCOPE_REV = 'startup-error-scope-20260920-r9';"

if new_marker in text:
    raise SystemExit("r9 already applied")
if expected_sha_marker not in text:
    raise SystemExit("required r8 marker not found")

text = text.replace(
    expected_sha_marker,
    expected_sha_marker + "\n  " + new_marker,
    1
)

old = """  window.addEventListener('error', event => {
    hkStartupFailure('error', event?.error || event?.message || event);
  }, true);

  window.addEventListener('unhandledrejection', event => {
    hkStartupFailure('promise', event?.reason || event);
  }, true);
"""

new = """  const hkStartupTrapActive = () => (
    hkStartupStage === 'BOOT' ||
    hkStartupStage === 'WAIT_BODY' ||
    hkStartupStage === 'BODY' ||
    hkStartupStage === 'RENDER'
  );

  const hkStartupErrorHandler = event => {
    if (!hkStartupTrapActive()) return;
    const filename = String(event?.filename || '');
    const message = String(event?.message || '');
    if (filename && !filename.includes('/panel.js') && !filename.includes('HamsterKingMobile')) return;
    if (!filename && message === 'Script error.') return;
    hkStartupFailure('error', event?.error || event?.message || event);
  };

  const hkStartupRejectionHandler = event => {
    if (!hkStartupTrapActive()) return;
    hkStartupFailure('promise', event?.reason || event);
  };

  window.addEventListener('error', hkStartupErrorHandler, true);
  window.addEventListener('unhandledrejection', hkStartupRejectionHandler, true);

  function disarmStartupErrorTrap() {
    try { window.removeEventListener('error', hkStartupErrorHandler, true); } catch (_) {}
    try { window.removeEventListener('unhandledrejection', hkStartupRejectionHandler, true); } catch (_) {}
  }
"""

if old not in text:
    raise SystemExit("r8 listener block not found")
text = text.replace(old, new, 1)

old_ready = "    hkStartupStage = 'READY';\n"
new_ready = "    hkStartupStage = 'READY';\n    disarmStartupErrorTrap();\n"
if old_ready not in text:
    raise SystemExit("READY marker not found")
text = text.replace(old_ready, new_ready, 1)

path.write_text(text, encoding="utf-8")
print("PATCH_R9_OK")
