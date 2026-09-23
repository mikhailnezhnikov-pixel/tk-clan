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
    "// @version      1.17.75\n",
    "// @version      1.17.76\n// @release-note Smoke-test: в шапке панели появился локальный статус Rat Hunt / War / Районов; сводка также попадает в Diagnostics JSON без новых запросов к игре.\n",
    'metadata version'
)
replace_once(
    "const BUILD_VERSION = '1.17.75';",
    "const BUILD_VERSION = '1.17.76';",
    'build version'
)
replace_once(
    "  const HK_RUNTIME_SMOKE_SESSION_REV = 'runtime-smoke-session-20260923-r1';\n",
    "  const HK_RUNTIME_SMOKE_SESSION_REV = 'runtime-smoke-session-20260923-r1';\n"
    "  const HK_RUNTIME_SMOKE_STATUS_REV = 'runtime-smoke-status-20260923-r1';\n",
    'status marker'
)

replace_once(
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
"""  function recordDiagnostic(type, data = {}) {
    let safe = {};
    try { safe = JSON.parse(JSON.stringify(data, (_key, value) => typeof value === 'string' ? diagnosticRedact(value) : value)); }
    catch (_) { safe = {value:diagnosticRedact(data)}; }
    const event={at:new Date().toISOString(), type:String(type || 'event'), data:safe};
    diagnostic.events.push(event);
    diagnosticPersistRuntimeSmokeEvent(event);
    if (diagnostic.events.length > DIAGNOSTIC_MAX_EVENTS) diagnostic.events.splice(0, diagnostic.events.length - DIAGNOSTIC_MAX_EVENTS);
    if(event.type.startsWith('runtime-smoke-'))try{renderRuntimeSmokeStatus();}catch(_){}
  }
""",
    'record diagnostic status refresh'
)

needle = """  function setHealth(name, ok, detail = '') {
"""
insert = """  function runtimeSmokeModuleState(prefix) {
    const rows=diagnostic.events.filter(row=>String(row?.type||'').startsWith('runtime-smoke-'+prefix));
    if(!rows.length)return {state:'idle',label:either('не запускалось','not run'),events:0,lastAt:null};
    let state='data',label=either('есть данные','has data');
    const terminals=rows.filter(row=>/-complete$|-error$/.test(String(row?.type||'')));
    const last=terminals[terminals.length-1]||rows[rows.length-1];
    const type=String(last?.type||'');
    if(type.endsWith('-error')){state='error';label=either('ошибка','error');}
    else if(type.endsWith('-complete')){state='complete';label=either('завершено','completed');}
    return {state,label,events:rows.length,lastAt:last?.at||rows[rows.length-1]?.at||null};
  }
  function runtimeSmokeSummary() {
    return {
      revision:HK_RUNTIME_SMOKE_STATUS_REV,
      ratHunt:runtimeSmokeModuleState('rat-hunt'),
      war:runtimeSmokeModuleState('war'),
      neighborhoods:runtimeSmokeModuleState('neighborhood')
    };
  }
  function renderRuntimeSmokeStatus() {
    const host=root?.querySelector?.('#hk-smoke-status');
    if(!host)return;
    const summary=runtimeSmokeSummary();
    const rows=[
      [either('Rat Hunt','Rat Hunt'),summary.ratHunt],
      [either('Война','War'),summary.war],
      [either('Районы','Neighborhoods'),summary.neighborhoods]
    ];
    const tone=state=>state==='complete'?'#6ee7a8':state==='error'?'#ff7b7b':state==='data'?'#ffd166':'#9aa8bc';
    host.innerHTML='<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px"><b>'+either('Smoke-test','Smoke test')+'</b><small style="color:#9aa8bc">'+escapeHtml(BUILD_VERSION)+'</small></div>'+
      '<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px">'+rows.map(([name,row])=>
        '<div style="padding:7px 8px;border:1px solid #304057;border-radius:9px;background:#101927;min-width:0"><small style="display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+escapeHtml(name)+'</small><b style="display:block;color:'+tone(row.state)+'">'+escapeHtml(row.label)+'</b><small style="color:#7f8da3">'+row.events+' '+either('событ.','events')+'</small></div>'
      ).join('')+'</div>';
  }

"""
if needle not in s:
    raise SystemExit('setHealth anchor missing')
s = s.replace(needle, insert + needle, 1)

replace_once(
"""      runtimeSmoke:{revision:HK_RUNTIME_SMOKE_SESSION_REV,persisted:true,sessionKeyVersion:1},
""",
"""      runtimeSmoke:{revision:HK_RUNTIME_SMOKE_SESSION_REV,persisted:true,sessionKeyVersion:1,summary:runtimeSmokeSummary()},
""",
    'report smoke summary'
)

replace_once(
"""      <div class="hk-health-actions"><button id="hk-health-check" class="hk-secondary">\${either('Проверить связь','Check connection')}</button><button id="hk-diagnostic">\${either('Диагностика','Diagnostics')}</button></div>
      <div id="hk-update-banner" class="hk-update"></div>
""",
"""      <div class="hk-health-actions"><button id="hk-health-check" class="hk-secondary">\${either('Проверить связь','Check connection')}</button><button id="hk-diagnostic">\${either('Диагностика','Diagnostics')}</button></div>
      <div id="hk-smoke-status" style="margin:8px 12px 0;padding:9px;border:1px solid #243449;border-radius:11px;background:#0d1521"></div>
      <div id="hk-update-banner" class="hk-update"></div>
""",
    'smoke status UI'
)

replace_once(
"""    renderHealth(); renderRunnerState(); renderGrowth();
""",
"""    renderHealth(); renderRunnerState(); renderGrowth(); renderRuntimeSmokeStatus();
""",
    'initial smoke render'
)

if "// @version      1.17.76" not in s or "const BUILD_VERSION = '1.17.76';" not in s:
    raise SystemExit('version patch failed')
for marker in [
    "runtime-smoke-observability-20260923-r1",
    "runtime-smoke-session-20260923-r1",
    "runtime-smoke-status-20260923-r1",
    "treasure-guide-priority-bundles-20260923-r1"
]:
    if marker not in s:
        raise SystemExit(f'missing marker: {marker}')
if s.count('id="hk-smoke-status"') != 1:
    raise SystemExit('smoke UI count mismatch')
if s.count("function runtimeSmokeSummary()") != 1:
    raise SystemExit('smoke summary function mismatch')

path.write_text(s, encoding='utf-8')
print('PATCH_1_17_76_RUNTIME_SMOKE_STATUS=PASS')
