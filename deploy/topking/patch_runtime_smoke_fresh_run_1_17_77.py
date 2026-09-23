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
    "// @version      1.17.76\n",
    "// @version      1.17.77\n// @release-note Smoke-test: статус теперь отражает именно последний запуск, а отдельная кнопка очищает только smoke-историю перед новым прогоном.\n",
    'metadata version'
)
replace_once(
    "const BUILD_VERSION = '1.17.76';",
    "const BUILD_VERSION = '1.17.77';",
    'build version'
)
replace_once(
    "  const HK_RUNTIME_SMOKE_STATUS_REV = 'runtime-smoke-status-20260923-r1';\n",
    "  const HK_RUNTIME_SMOKE_STATUS_REV = 'runtime-smoke-status-20260923-r1';\n"
    "  const HK_RUNTIME_SMOKE_FRESH_RUN_REV = 'runtime-smoke-fresh-run-20260923-r1';\n",
    'fresh run marker'
)

old = """  function runtimeSmokeModuleState(prefix) {
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
"""
new = """  function runtimeSmokeModuleState(prefix) {
    const rows=diagnostic.events.filter(row=>String(row?.type||'').startsWith('runtime-smoke-'+prefix));
    if(!rows.length)return {state:'idle',label:either('не запускалось','not run'),events:0,lastAt:null};
    let state='data',label=either('есть данные','has data');
    const last=rows[rows.length-1];
    const type=String(last?.type||'');
    if(type.endsWith('-error')){state='error';label=either('ошибка','error');}
    else if(type.endsWith('-complete')){state='complete';label=either('завершено','completed');}
    return {state,label,events:rows.length,lastAt:last?.at||null};
  }
  function runtimeSmokeReset() {
    diagnostic.events=diagnostic.events.filter(row=>!String(row?.type||'').startsWith('runtime-smoke-'));
    try{sessionStorage.removeItem(HK_RUNTIME_SMOKE_SESSION_KEY);}catch(_){}
    renderRuntimeSmokeStatus();
  }
"""
replace_once(old,new,'module state/reset')

old = """    host.innerHTML='<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px"><b>'+either('Smoke-test','Smoke test')+'</b><small style="color:#9aa8bc">'+escapeHtml(BUILD_VERSION)+'</small></div>'+
      '<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px">'+rows.map(([name,row])=>
        '<div style="padding:7px 8px;border:1px solid #304057;border-radius:9px;background:#101927;min-width:0"><small style="display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+escapeHtml(name)+'</small><b style="display:block;color:'+tone(row.state)+'">'+escapeHtml(row.label)+'</b><small style="color:#7f8da3">'+row.events+' '+either('событ.','events')+'</small></div>'
      ).join('')+'</div>';
"""
new = """    host.innerHTML='<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px"><b>'+either('Smoke-test','Smoke test')+'</b><div style="display:flex;align-items:center;gap:7px"><small style="color:#9aa8bc">'+escapeHtml(BUILD_VERSION)+'</small><button id="hk-smoke-reset" type="button" class="hk-secondary" style="padding:4px 7px;font-size:11px">'+either('Сбросить','Reset')+'</button></div></div>'+
      '<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px">'+rows.map(([name,row])=>
        '<div style="padding:7px 8px;border:1px solid #304057;border-radius:9px;background:#101927;min-width:0"><small style="display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+escapeHtml(name)+'</small><b style="display:block;color:'+tone(row.state)+'">'+escapeHtml(row.label)+'</b><small style="color:#7f8da3">'+row.events+' '+either('событ.','events')+'</small></div>'
      ).join('')+'</div>';
    const reset=host.querySelector('#hk-smoke-reset');
    if(reset)reset.onclick=runtimeSmokeReset;
"""
replace_once(old,new,'status render reset')

if "// @version      1.17.77" not in s or "const BUILD_VERSION = '1.17.77';" not in s:
    raise SystemExit('version patch failed')
for marker in [
    "runtime-smoke-observability-20260923-r1",
    "runtime-smoke-session-20260923-r1",
    "runtime-smoke-status-20260923-r1",
    "runtime-smoke-fresh-run-20260923-r1",
    "treasure-guide-priority-bundles-20260923-r1"
]:
    if marker not in s:
        raise SystemExit(f'missing marker: {marker}')
if s.count("function runtimeSmokeReset()") != 1:
    raise SystemExit('reset function mismatch')
if s.count('id="hk-smoke-reset"') != 1:
    raise SystemExit('reset button mismatch')
if "const terminals=rows.filter" in s:
    raise SystemExit('stale terminal logic still present')

path.write_text(s, encoding='utf-8')
print('PATCH_1_17_77_RUNTIME_SMOKE_FRESH_RUN=PASS')
