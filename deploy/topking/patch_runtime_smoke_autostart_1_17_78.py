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
    "// @version      1.17.77\n",
    "// @version      1.17.78\n// @release-note Smoke-test: каждый Rat Hunt / War / Районы автоматически начинает чистую историю своего модуля; добавлен отдельный экспорт Smoke JSON без игровых запросов.\n",
    'metadata version'
)
replace_once(
    "const BUILD_VERSION = '1.17.77';",
    "const BUILD_VERSION = '1.17.78';",
    'build version'
)
replace_once(
    "  const HK_RUNTIME_SMOKE_FRESH_RUN_REV = 'runtime-smoke-fresh-run-20260923-r1';\n",
    "  const HK_RUNTIME_SMOKE_FRESH_RUN_REV = 'runtime-smoke-fresh-run-20260923-r1';\n"
    "  const HK_RUNTIME_SMOKE_AUTOSTART_REV = 'runtime-smoke-autostart-20260923-r1';\n",
    'autostart marker'
)

replace_once(
"""  function runtimeSmokeReset() {
    diagnostic.events=diagnostic.events.filter(row=>!String(row?.type||'').startsWith('runtime-smoke-'));
    try{sessionStorage.removeItem(HK_RUNTIME_SMOKE_SESSION_KEY);}catch(_){}
    renderRuntimeSmokeStatus();
  }
""",
"""  function runtimeSmokeRewriteSession() {
    try{
      const rows=diagnostic.events.filter(row=>String(row?.type||'').startsWith('runtime-smoke-')).slice(-160);
      if(rows.length)sessionStorage.setItem(HK_RUNTIME_SMOKE_SESSION_KEY,JSON.stringify(rows));
      else sessionStorage.removeItem(HK_RUNTIME_SMOKE_SESSION_KEY);
    }catch(_){}
  }
  function runtimeSmokeResetModule(prefix) {
    const marker='runtime-smoke-'+String(prefix||'');
    diagnostic.events=diagnostic.events.filter(row=>!String(row?.type||'').startsWith(marker));
    runtimeSmokeRewriteSession();
    renderRuntimeSmokeStatus();
  }
  function runtimeSmokeReset() {
    diagnostic.events=diagnostic.events.filter(row=>!String(row?.type||'').startsWith('runtime-smoke-'));
    runtimeSmokeRewriteSession();
    renderRuntimeSmokeStatus();
  }
""",
    'reset helpers'
)

replace_once(
"""  function downloadDiagnosticReport() {
""",
"""  function downloadRuntimeSmokeReport() {
    const report={
      schema:'topking-hk-runtime-smoke-v1',
      version:VERSION,
      revision:HK_RUNTIME_SMOKE_AUTOSTART_REV,
      exportedAt:new Date().toISOString(),
      summary:runtimeSmokeSummary(),
      runner:{...hkRunner.state},
      events:diagnostic.events.filter(row=>String(row?.type||'').startsWith('runtime-smoke-'))
    };
    const blob=new Blob([JSON.stringify(report,null,2)],{type:'application/json;charset=utf-8'});
    const url=URL.createObjectURL(blob);
    const link=document.createElement('a');
    link.href=url;
    link.download='HK_smoke_'+new Date().toISOString().replace(/[:.]/g,'-')+'.json';
    document.body.appendChild(link);link.click();link.remove();
    setTimeout(()=>URL.revokeObjectURL(url),1200);
  }
  function downloadDiagnosticReport() {
""",
    'smoke report exporter'
)

replace_once(
"""    host.innerHTML='<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px"><b>'+either('Smoke-test','Smoke test')+'</b><div style="display:flex;align-items:center;gap:7px"><small style="color:#9aa8bc">'+escapeHtml(BUILD_VERSION)+'</small><button id="hk-smoke-reset" type="button" class="hk-secondary" style="padding:4px 7px;font-size:11px">'+either('Сбросить','Reset')+'</button></div></div>'+
""",
"""    host.innerHTML='<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px"><b>'+either('Smoke-test','Smoke test')+'</b><div style="display:flex;align-items:center;gap:7px"><small style="color:#9aa8bc">'+escapeHtml(BUILD_VERSION)+'</small><button id="hk-smoke-export" type="button" class="hk-secondary" style="padding:4px 7px;font-size:11px">JSON</button><button id="hk-smoke-reset" type="button" class="hk-secondary" style="padding:4px 7px;font-size:11px">'+either('Сбросить','Reset')+'</button></div></div>'+
""",
    'smoke header export button'
)

replace_once(
"""    const reset=host.querySelector('#hk-smoke-reset');
    if(reset)reset.onclick=runtimeSmokeReset;
""",
"""    const exportButton=host.querySelector('#hk-smoke-export');
    if(exportButton)exportButton.onclick=downloadRuntimeSmokeReport;
    const reset=host.querySelector('#hk-smoke-reset');
    if(reset)reset.onclick=runtimeSmokeReset;
""",
    'smoke header handlers'
)

replace_once(
"""    )))return;

    hkRunner.start({title:either('Охота на крыс','Rat Hunt'),total:rounds,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});
""",
"""    )))return;

    runtimeSmokeResetModule('rat-hunt');
    hkRuntimeSmokeRecord('rat-hunt-start',{
      rounds,
      paymentMode:String(selectedPlan?.paymentMode||''),
      presetId:String(ratHuntCombat.presetId||'').slice(0,100),
      maxRestoration:pitCanonWhole(ratHuntCombat.maxRestoration)
    });
    hkRunner.start({title:either('Охота на крыс','Rat Hunt'),total:rounds,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});
""",
    'rat hunt smoke start'
)

replace_once(
"""    )))return;

    hkRunner.start({title:either('Войны','Wars'),total:steps.length,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});
""",
"""    )))return;

    runtimeSmokeResetModule('war');
    hkRuntimeSmokeRecord('war-start',{
      steps:steps.length,
      paymentMode:String(plan?.paymentMode||''),
      warId:String(activeWar?.id||'').slice(0,100),
      freePasses:pitCanonWhole(warCombat.available)
    });
    hkRunner.start({title:either('Войны','Wars'),total:steps.length,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});
""",
    'war smoke start'
)

replace_once(
"""    )))return;
    try{
      const liveView=await apiJson('/idler/view','GET',null,true,1);
      neighborhoodApplyIdler(liveView,'neighborhood:run-preflight');
    }catch(error){
      log(either('Не удалось повторно проверить Районы перед запуском','Could not revalidate Neighborhoods before start')+': '+(error?.message||error),'warn');
      return;
    }
    hkRunner.start({title:either('Районы','Neighborhoods'),total,step:either('Синхронизация угроз','Syncing threats'),pausable:true,stoppable:true});
""",
"""    )))return;
    runtimeSmokeResetModule('neighborhood');
    hkRuntimeSmokeRecord('neighborhood-start',{
      selected:enemies.length,
      totalLevels:total,
      tapPower:Number(neighborhoodIdler?.player_tap_power??0)
    });
    try{
      const liveView=await apiJson('/idler/view','GET',null,true,1);
      neighborhoodApplyIdler(liveView,'neighborhood:run-preflight');
    }catch(error){
      hkRuntimeSmokeRecord('neighborhood-error',{
        stage:'run-preflight',
        name:String(error?.name||''),
        status:Number(error?.httpStatus||0),
        message:String(error?.message||error||'').slice(0,500)
      });
      log(either('Не удалось повторно проверить Районы перед запуском','Could not revalidate Neighborhoods before start')+': '+(error?.message||error),'warn');
      return;
    }
    hkRunner.start({title:either('Районы','Neighborhoods'),total,step:either('Синхронизация угроз','Syncing threats'),pausable:true,stoppable:true});
""",
    'neighborhood smoke start'
)

if "// @version      1.17.78" not in s or "const BUILD_VERSION = '1.17.78';" not in s:
    raise SystemExit('version patch failed')
for marker in [
    "runtime-smoke-observability-20260923-r1",
    "runtime-smoke-session-20260923-r1",
    "runtime-smoke-status-20260923-r1",
    "runtime-smoke-fresh-run-20260923-r1",
    "runtime-smoke-autostart-20260923-r1",
    "treasure-guide-priority-bundles-20260923-r1"
]:
    if marker not in s:
        raise SystemExit(f'missing marker: {marker}')
for needle in [
    "hkRuntimeSmokeRecord('rat-hunt-start'",
    "hkRuntimeSmokeRecord('war-start'",
    "hkRuntimeSmokeRecord('neighborhood-start'",
    "function downloadRuntimeSmokeReport()",
    'id="hk-smoke-export"'
]:
    if s.count(needle) != 1:
        raise SystemExit(f'expected one occurrence: {needle} -> {s.count(needle)}')

path.write_text(s, encoding='utf-8')
print('PATCH_1_17_78_RUNTIME_SMOKE_AUTOSTART=PASS')
