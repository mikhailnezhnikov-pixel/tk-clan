from pathlib import Path

path=Path('/tmp/HamsterKingMobile.user.js')
s=path.read_text(encoding='utf-8')

def replace_once(old,new,label):
    global s
    count=s.count(old)
    if count!=1:
        raise SystemExit(f'{label}: expected 1 match, got {count}')
    s=s.replace(old,new,1)

replace_once(
    "// @version      1.17.79\n",
    "// @version      1.17.80\n// @release-note Smoke-test: Rat Hunt / War / Районы показывают покрытие контрольных точек старт → мутация → завершение; это индикатор полноты доказательств, а не автоматический runtime PASS.\n",
    'metadata version'
)
replace_once("const BUILD_VERSION = '1.17.79';","const BUILD_VERSION = '1.17.80';",'build version')
replace_once(
    "  const HK_RUNTIME_SMOKE_AUTOSTART_REV = 'runtime-smoke-autostart-20260923-r1';\n",
    "  const HK_RUNTIME_SMOKE_AUTOSTART_REV = 'runtime-smoke-autostart-20260923-r1';\n"
    "  const HK_RUNTIME_SMOKE_COVERAGE_REV = 'runtime-smoke-coverage-20260923-r1';\n",
    'coverage marker'
)

old="""  function runtimeSmokeModuleState(prefix) {
    const rows=diagnostic.events.filter(row=>String(row?.type||'').startsWith('runtime-smoke-'+prefix));
    if(!rows.length)return {state:'idle',label:either('не запускалось','not run'),events:0,lastAt:null};
    let state='data',label=either('есть данные','has data');
    const last=rows[rows.length-1];
    const type=String(last?.type||'');
    if(type.endsWith('-error')){state='error';label=either('ошибка','error');}
    else if(type.endsWith('-complete')){state='complete';label=either('завершено','completed');}
    return {state,label,events:rows.length,lastAt:last?.at||null};
  }
"""
new=r"""  function runtimeSmokeCoverage(prefix,rows) {
    const types=rows.map(row=>String(row?.type||''));
    const started=types.includes('runtime-smoke-'+prefix+'-start');
    let mutation=false;
    if(prefix==='rat-hunt'){
      mutation=rows.some(row=>String(row?.type||'')==='runtime-smoke-rat-hunt-state'&&/^rat-hunt:(?:change-preset|start|battle|respawn|finish)$/.test(String(row?.data?.reason||'')));
    }else if(prefix==='war'){
      mutation=rows.some(row=>String(row?.type||'')==='runtime-smoke-war-state'&&String(row?.data?.reason||'')==='war-combat:fight');
    }else if(prefix==='neighborhood'){
      mutation=rows.some(row=>String(row?.type||'')==='runtime-smoke-neighborhood-state'&&/^neighborhood:\/idler\/(?:claim|update|level|tap)$/.test(String(row?.data?.reason||'')));
    }
    const completed=types.includes('runtime-smoke-'+prefix+'-complete');
    const checks={start:started,mutation,complete:completed};
    const missing=Object.entries(checks).filter(([,ok])=>!ok).map(([key])=>key);
    return {revision:HK_RUNTIME_SMOKE_COVERAGE_REV,...checks,count:Object.values(checks).filter(Boolean).length,total:3,missing};
  }
  function runtimeSmokeModuleState(prefix) {
    const rows=diagnostic.events.filter(row=>String(row?.type||'').startsWith('runtime-smoke-'+prefix));
    const coverage=runtimeSmokeCoverage(prefix,rows);
    if(!rows.length)return {state:'idle',label:either('не запускалось','not run'),events:0,lastAt:null,coverage};
    let state='data',label=either('есть данные','has data');
    const last=rows[rows.length-1];
    const type=String(last?.type||'');
    if(type.endsWith('-error')){state='error';label=either('ошибка','error');}
    else if(type.endsWith('-complete')){state='complete';label=either('завершено','completed');}
    return {state,label,events:rows.length,lastAt:last?.at||null,coverage};
  }
"""
replace_once(old,new,'module state coverage')

old="""    const tone=state=>state==='complete'?'#6ee7a8':state==='error'?'#ff7b7b':state==='data'?'#ffd166':'#9aa8bc';
    host.innerHTML='<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px"><b>'+either('Smoke-test','Smoke test')+'</b><div style="display:flex;align-items:center;gap:7px"><small style="color:#9aa8bc">'+escapeHtml(BUILD_VERSION)+'</small><button id="hk-smoke-export" type="button" class="hk-secondary" style="padding:4px 7px;font-size:11px">JSON</button><button id="hk-smoke-reset" type="button" class="hk-secondary" style="padding:4px 7px;font-size:11px">'+either('Сбросить','Reset')+'</button></div></div>'+
      '<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px">'+rows.map(([name,row])=>
        '<div style="padding:7px 8px;border:1px solid #304057;border-radius:9px;background:#101927;min-width:0"><small style="display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+escapeHtml(name)+'</small><b style="display:block;color:'+tone(row.state)+'">'+escapeHtml(row.label)+'</b><small style="color:#7f8da3">'+row.events+' '+either('событ.','events')+'</small></div>'
      ).join('')+'</div>';
"""
new="""    const tone=row=>row?.state==='error'?'#ff7b7b':row?.state==='complete'&&row?.coverage?.count===3?'#6ee7a8':row?.state==='idle'?'#9aa8bc':'#ffd166';
    host.innerHTML='<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px"><b>'+either('Smoke-test','Smoke test')+'</b><div style="display:flex;align-items:center;gap:7px"><small style="color:#9aa8bc">'+escapeHtml(BUILD_VERSION)+'</small><button id="hk-smoke-export" type="button" class="hk-secondary" style="padding:4px 7px;font-size:11px">JSON</button><button id="hk-smoke-reset" type="button" class="hk-secondary" style="padding:4px 7px;font-size:11px">'+either('Сбросить','Reset')+'</button></div></div>'+
      '<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px">'+rows.map(([name,row])=>
        '<div style="padding:7px 8px;border:1px solid #304057;border-radius:9px;background:#101927;min-width:0" title="'+escapeHtml((row?.coverage?.missing||[]).join(', '))+'"><small style="display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+escapeHtml(name)+'</small><b style="display:block;color:'+tone(row)+'">'+escapeHtml(row.label)+'</b><small style="display:block;color:#7f8da3">'+row.events+' '+either('событ.','events')+'</small><small style="display:block;color:'+(row?.coverage?.count===3?'#6ee7a8':'#9aa8bc')+'">'+either('контроль','coverage')+' '+Number(row?.coverage?.count||0)+'/3</small></div>'
      ).join('')+'</div>';
"""
replace_once(old,new,'coverage UI')

if "// @version      1.17.80" not in s or "const BUILD_VERSION = '1.17.80';" not in s:
    raise SystemExit('version patch failed')
for marker in [
    "runtime-smoke-observability-20260923-r1",
    "runtime-smoke-session-20260923-r1",
    "runtime-smoke-status-20260923-r1",
    "runtime-smoke-fresh-run-20260923-r1",
    "runtime-smoke-autostart-20260923-r1",
    "runtime-smoke-coverage-20260923-r1",
    "treasure-guide-bundle-card-dom-20260923-r1"
]:
    if marker not in s:
        raise SystemExit('missing marker: '+marker)
if s.count("function runtimeSmokeCoverage(")!=1:
    raise SystemExit('coverage function mismatch')

path.write_text(s,encoding='utf-8')
print('PATCH_1_17_80_RUNTIME_SMOKE_COVERAGE=PASS')
