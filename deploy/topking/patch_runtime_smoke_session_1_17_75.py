from pathlib import Path

path = Path('/tmp/HamsterKingMobile.user.js')
s = path.read_text(encoding='utf-8')

def replace_once(old, new, label):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 match, got {count}')
    s = s.replace(old, new, 1)

replace_once(
    "// @version      1.17.74\n",
    "// @version      1.17.75\n// @release-note Диагностика smoke-test: события Rat Hunt / War / Районов теперь переживают перезагрузку текущей вкладки через sessionStorage; сохраняются только обезличенные runtime-smoke события.\n",
    'metadata version'
)
replace_once(
    "const BUILD_VERSION = '1.17.74';",
    "const BUILD_VERSION = '1.17.75';",
    'build version'
)
replace_once(
    "  const HK_RUNTIME_SMOKE_OBSERVABILITY_REV = 'runtime-smoke-observability-20260923-r1';\n",
    "  const HK_RUNTIME_SMOKE_OBSERVABILITY_REV = 'runtime-smoke-observability-20260923-r1';\n"
    "  const HK_RUNTIME_SMOKE_SESSION_REV = 'runtime-smoke-session-20260923-r1';\n",
    'session marker'
)

replace_once(
"""  const diagnostic = {startedAt:new Date().toISOString(), events:[]};
  const healthState = {
""",
"""  const HK_RUNTIME_SMOKE_SESSION_KEY='hk_runtime_smoke_events_v1';
  function diagnosticLoadRuntimeSmokeEvents(){
    try{
      const value=JSON.parse(sessionStorage.getItem(HK_RUNTIME_SMOKE_SESSION_KEY)||'[]');
      return Array.isArray(value)?value.filter(row=>String(row?.type||'').startsWith('runtime-smoke-')).slice(-160):[];
    }catch(_){return[];}
  }
  function diagnosticPersistRuntimeSmokeEvent(event){
    if(!event||!String(event.type||'').startsWith('runtime-smoke-'))return;
    try{
      const current=JSON.parse(sessionStorage.getItem(HK_RUNTIME_SMOKE_SESSION_KEY)||'[]');
      const rows=Array.isArray(current)?current.filter(row=>String(row?.type||'').startsWith('runtime-smoke-')):[];
      rows.push(event);
      sessionStorage.setItem(HK_RUNTIME_SMOKE_SESSION_KEY,JSON.stringify(rows.slice(-160)));
    }catch(_){}
  }
  const diagnostic = {startedAt:new Date().toISOString(), events:diagnosticLoadRuntimeSmokeEvents()};
  const healthState = {
""",
    'diagnostic session bootstrap'
)

replace_once(
"""  function recordDiagnostic(type, data = {}) {
    let safe = {};
    try { safe = JSON.parse(JSON.stringify(data, (_key, value) => typeof value === 'string' ? diagnosticRedact(value) : value)); }
    catch (_) { safe = {value:diagnosticRedact(data)}; }
    diagnostic.events.push({at:new Date().toISOString(), type:String(type || 'event'), data:safe});
    if (diagnostic.events.length > DIAGNOSTIC_MAX_EVENTS) diagnostic.events.splice(0, diagnostic.events.length - DIAGNOSTIC_MAX_EVENTS);
  }
""",
"""  function recordDiagnostic(type, data = {}) {
    let safe = {};
    try { safe = JSON.parse(JSON.stringify(data, (_key, value) => typeof value === 'string' ? diagnosticRedact(value) : value)); }
    catch (_) { safe = {value:diagnosticRedact(data)}; }
    const event={at:new Date().toISOString(), type:String(type || 'event'), data:safe};
    diagnostic.events.push(event);
    diagnosticPersistRuntimeSmokeEvent(event);
    if (diagnostic.events.length > DIAGNOSTIC_MAX_EVENTS) diagnostic.events.splice(0, diagnostic.events.length - DIAGNOSTIC_MAX_EVENTS);
  }
""",
    'recordDiagnostic persistence'
)

replace_once(
"""      schema:'topking-hk-diagnostic-v1', version:VERSION, startedAt:diagnostic.startedAt, exportedAt:new Date().toISOString(),
""",
"""      schema:'topking-hk-diagnostic-v1', version:VERSION, startedAt:diagnostic.startedAt, exportedAt:new Date().toISOString(),
      runtimeSmoke:{revision:HK_RUNTIME_SMOKE_SESSION_REV,persisted:true,sessionKeyVersion:1},
""",
    'diagnostic report metadata'
)

if "runtime-smoke-session-20260923-r1" not in s:
    raise SystemExit('session marker missing')
if "// @version      1.17.75" not in s or "const BUILD_VERSION = '1.17.75';" not in s:
    raise SystemExit('version patch failed')
if s.count("diagnosticPersistRuntimeSmokeEvent(event);") != 1:
    raise SystemExit('persistence hook mismatch')
if "runtime-smoke-observability-20260923-r1" not in s:
    raise SystemExit('observability marker lost')

path.write_text(s, encoding='utf-8')
print('PATCH_1_17_75_RUNTIME_SMOKE_SESSION=PASS')
