from pathlib import Path

TARGET=Path('/tmp/HamsterKingMobile.user.js')
REV='startup-error-trap-20260920-r8'
MARKER=f"HK_STARTUP_ERROR_TRAP_REV = '{REV}'"

def require(s,n,l):
    if n not in s: raise SystemExit(f'startup error trap check failed: {l}')
def rep(s,o,n,l):
    if n in s: return s
    if o not in s: raise SystemExit(f'startup error trap anchor missing: {l}')
    return s.replace(o,n,1)

def apply(s):
    require(s,"HK_STARTUP_STAGE_REV = 'startup-stages-20260920-r7'",'startup stages r7')
    require(s,"HK_CORE_REVISION = 'core-20260920-r6'",'core r6')
    if MARKER in s: return validate(s)

    s=rep(s,
        "  const HK_STARTUP_STAGE_REV = 'startup-stages-20260920-r7';",
        "  const HK_STARTUP_STAGE_REV = 'startup-stages-20260920-r7';\n  const "+MARKER+";",
        'marker')

    anchor="""  function hideBootstrap() { bootstrapButton?.remove(); }
  showBootstrap();"""

    replacement="""  function hideBootstrap() { bootstrapButton?.remove(); }

  function hkStartupFailure(kind, value) {
    try {
      hkStartupStage = 'ERROR';
      const message = String(
        value?.stack ||
        value?.message ||
        value?.reason?.stack ||
        value?.reason?.message ||
        value ||
        'unknown startup error'
      ).slice(0, 1800);
      showBootstrap(kind + ': ' + message);
    } catch (_) {}
  }

  window.addEventListener('error', event => {
    hkStartupFailure('error', event?.error || event?.message || event);
  }, true);

  window.addEventListener('unhandledrejection', event => {
    hkStartupFailure('promise', event?.reason || event);
  }, true);

  showBootstrap();"""

    s=rep(s,anchor,replacement,'global startup error trap')

    return validate(s)

def validate(s):
    for n in [
        MARKER,
        "function hkStartupFailure(kind, value)",
        "hkStartupStage = 'ERROR'",
        "window.addEventListener('error'",
        "window.addEventListener('unhandledrejection'",
        "showBootstrap(kind + ': ' + message)",
        "HK_STARTUP_STAGE_REV = 'startup-stages-20260920-r7'",
    ]: require(s,n,n)
    return s

if __name__=='__main__':
    s=TARGET.read_text(encoding='utf-8')
    TARGET.write_text(apply(s),encoding='utf-8')
    print('HK_STARTUP_ERROR_TRAP_R8_OK')
