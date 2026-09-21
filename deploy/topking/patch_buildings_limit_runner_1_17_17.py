from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")

required=[
    "// @version      1.17.16",
    "const BUILD_VERSION = '1.17.16';",
    "const HK_CORE_REVISION = 'core-20260921-r18-buildings-active-fix';",
    "const HK_BUILDINGS_ACTIVE_REV = 'buildings-active-semantics-20260921-r1';",
    "function buildingCanonSettings()",
    "function renderRunnerState()",
    "async function runBuildingsCanonical()",
    "function renderBuildings()",
]
for marker in required:
    if marker not in s:
        raise SystemExit(f"missing expected marker: {marker}")

s=s.replace("// @version      1.17.16","// @version      1.17.17",1)
s=s.replace(
    "// @release-note Исправлен расчёт активных зданий: план и запуск теперь используют реальные активные слоты игры.",
    "// @release-note Добавлен лимит открытия зданий: 1 / 10 / 15 / 20 / все доступные.\n"
    "// @release-note Runner «Здания» приведён к компактному визуальному канону панели.\n"
    "// @release-note Исправлен расчёт активных зданий: план и запуск теперь используют реальные активные слоты игры.",
    1,
)
s=s.replace("const BUILD_VERSION = '1.17.16';","const BUILD_VERSION = '1.17.17';",1)
s=s.replace(
    "const HK_CORE_REVISION = 'core-20260921-r18-buildings-active-fix';",
    "const HK_CORE_REVISION = 'core-20260921-r19-buildings-limit-runner';",
    1,
)
s=s.replace(
    "const HK_BUILDINGS_ACTIVE_REV = 'buildings-active-semantics-20260921-r1';",
    "const HK_BUILDINGS_ACTIVE_REV = 'buildings-active-semantics-20260921-r1';\n"
    "  const HK_BUILDINGS_LIMIT_REV = 'buildings-open-limit-20260921-r1';\n"
    "  const HK_BUILDINGS_RUNNER_UI_REV = 'buildings-runner-ui-20260921-r1';",
    1,
)

old_settings="""  function buildingCanonSettings() {
    const stored=load().buildingCanonSettings||{};
    return {
      minCrystals:Number.isSafeInteger(Number(stored.minCrystals))&&Number(stored.minCrystals)>=0?Number(stored.minCrystals):3,
      favoriteFrom:Number.isSafeInteger(Number(stored.favoriteFrom))&&Number(stored.favoriteFrom)>=0?Number(stored.favoriteFrom):2,
      buildingType:['all','normal','investment'].includes(String(stored.buildingType||''))?String(stored.buildingType):'normal'
    };
  }

  function buildingCanonSaveSettings(settings) {
    save({buildingCanonSettings:{
      minCrystals:Math.max(0,Math.trunc(Number(settings?.minCrystals)||0)),
      favoriteFrom:Math.max(0,Math.trunc(Number(settings?.favoriteFrom)||0)),
      buildingType:['all','normal','investment'].includes(String(settings?.buildingType||''))?String(settings.buildingType):'normal'
    }});
  }

  function buildingCanonReadSettingsFromDom() {
    const box=root?.querySelector('#hk-buildings-content');
    if(!box)return buildingCanonSettings();
    const settings={
      minCrystals:Math.max(0,Math.trunc(Number(box.querySelector('#hk-building-min-crystals')?.value)||0)),
      favoriteFrom:Math.max(0,Math.trunc(Number(box.querySelector('#hk-building-favorite-from')?.value)||0)),
      buildingType:String(box.querySelector('#hk-building-type')?.value||'normal')
    };
    if(!['all','normal','investment'].includes(settings.buildingType))settings.buildingType='normal';
    buildingCanonSaveSettings(settings);
    return settings;
  }
"""
new_settings="""  function buildingCanonSettings() {
    const stored=load().buildingCanonSettings||{};
    const rawLimit=stored.openLimit;
    const parsedLimit=String(rawLimit)==='all'||Number(rawLimit)===0?0:Number(rawLimit);
    return {
      minCrystals:Number.isSafeInteger(Number(stored.minCrystals))&&Number(stored.minCrystals)>=0?Number(stored.minCrystals):3,
      favoriteFrom:Number.isSafeInteger(Number(stored.favoriteFrom))&&Number(stored.favoriteFrom)>=0?Number(stored.favoriteFrom):2,
      buildingType:['all','normal','investment'].includes(String(stored.buildingType||''))?String(stored.buildingType):'normal',
      openLimit:[1,10,15,20].includes(parsedLimit)||parsedLimit===0?parsedLimit:1
    };
  }

  function buildingCanonSaveSettings(settings) {
    const rawLimit=Number(settings?.openLimit);
    const openLimit=[1,10,15,20].includes(rawLimit)||rawLimit===0?rawLimit:1;
    save({buildingCanonSettings:{
      minCrystals:Math.max(0,Math.trunc(Number(settings?.minCrystals)||0)),
      favoriteFrom:Math.max(0,Math.trunc(Number(settings?.favoriteFrom)||0)),
      buildingType:['all','normal','investment'].includes(String(settings?.buildingType||''))?String(settings.buildingType):'normal',
      openLimit
    }});
  }

  function buildingCanonReadSettingsFromDom() {
    const box=root?.querySelector('#hk-buildings-content');
    if(!box)return buildingCanonSettings();
    const limitValue=String(box.querySelector('#hk-building-open-limit')?.value||'1');
    const settings={
      minCrystals:Math.max(0,Math.trunc(Number(box.querySelector('#hk-building-min-crystals')?.value)||0)),
      favoriteFrom:Math.max(0,Math.trunc(Number(box.querySelector('#hk-building-favorite-from')?.value)||0)),
      buildingType:String(box.querySelector('#hk-building-type')?.value||'normal'),
      openLimit:limitValue==='all'?0:Number(limitValue)
    };
    if(!['all','normal','investment'].includes(settings.buildingType))settings.buildingType='normal';
    if(![0,1,10,15,20].includes(settings.openLimit))settings.openLimit=1;
    buildingCanonSaveSettings(settings);
    return settings;
  }
"""
if old_settings not in s:
    raise SystemExit("building settings block not found")
s=s.replace(old_settings,new_settings,1)

old_candidates="""      const capacity=buildingCanonPlan.capacity;
      const source=buildingCanonPlan.candidates;
      if(!source.length){log(either('Подходящих неактивных зданий нет.','No eligible inactive buildings.'),'warn');return;}
      if(capacity.free!==null&&capacity.free<=0){log(either('Подходящие здания есть, но свободных активных слотов нет.','Eligible buildings exist, but there are no free active-building slots.'),'warn');return;}
      const candidates=capacity.free===null?source:source.slice(0,capacity.free);
      const preview=candidates.slice(0,12).map((row,index)=>`${index+1}. ${row.buildingId} · 💎 ${row.crystals}${row.isInvest?' · ◆':''}`).join('\n');
      const more=candidates.length>12?either(`\n…и ещё ${candidates.length-12}`,`\n…and ${candidates.length-12} more`):'';
      if(!confirm(either(
        `Открыть подходящие здания: ${candidates.length}?\n\n${preview}${more}`,
        `Open eligible buildings: ${candidates.length}?\n\n${preview}${more}`
      )))return;
"""
new_candidates="""      const capacity=buildingCanonPlan.capacity;
      const source=buildingCanonPlan.candidates;
      if(!source.length){log(either('Подходящих неактивных зданий нет.','No eligible inactive buildings.'),'warn');return;}
      if(capacity.free!==null&&capacity.free<=0){log(either('Подходящие здания есть, но свободных активных слотов нет.','Eligible buildings exist, but there are no free active-building slots.'),'warn');return;}
      const capacityCandidates=capacity.free===null?source:source.slice(0,capacity.free);
      const limit=Number(buildingCanonPlan.settings?.openLimit);
      const candidates=limit===0?capacityCandidates:capacityCandidates.slice(0,Math.max(1,limit||1));
      const preview=candidates.slice(0,12).map((row,index)=>`${index+1}. ${row.buildingId} · 💎 ${row.crystals}${row.isInvest?' · ◆':''}`).join('\n');
      const more=candidates.length>12?either(`\n…и ещё ${candidates.length-12}`,`\n…and ${candidates.length-12} more`):'';
      if(!confirm(either(
        `Открыть зданий: ${candidates.length} из ${source.length} кандидатов?\n\n${preview}${more}`,
        `Open buildings: ${candidates.length} of ${source.length} candidates?\n\n${preview}${more}`
      )))return;
"""
if old_candidates not in s:
    raise SystemExit("runner candidate block not found")
s=s.replace(old_candidates,new_candidates,1)

old_runner_head="""    const state=hkRunner.state;
    const visibleState=state.status!=='idle',title=String(state.title||''),exploreRun=visibleState&&title===either('Исследование · E3','Explore · E3'); box.classList.toggle('show',visibleState);
    box.classList.toggle('pit-run',visibleState&&title===either('Ямы','Pits'));
    box.classList.toggle('explore-run',exploreRun);
"""
new_runner_head="""    const state=hkRunner.state;
    const visibleState=state.status!=='idle',title=String(state.title||''),exploreRun=visibleState&&title===either('Исследование · E3','Explore · E3'),buildingsRun=visibleState&&title===either('Здания','Buildings'); box.classList.toggle('show',visibleState);
    box.classList.toggle('pit-run',visibleState&&title===either('Ямы','Pits'));
    box.classList.toggle('explore-run',exploreRun);
    box.classList.toggle('buildings-run',buildingsRun);
"""
if old_runner_head not in s:
    raise SystemExit("runner class block not found")
s=s.replace(old_runner_head,new_runner_head,1)

old_state="""    root.querySelector('#hk-runner-title').textContent=state.title||either('Выполнение','Execution');
    root.querySelector('#hk-runner-state').textContent=labels[state.status]||state.status;
"""
new_state="""    root.querySelector('#hk-runner-title').textContent=state.title||either('Выполнение','Execution');
    const stateLabel=labels[state.status]||state.status;
    root.querySelector('#hk-runner-state').textContent=buildingsRun&&state.total?`${stateLabel} · ${state.done}/${state.total}`:stateLabel;
"""
if old_state not in s:
    raise SystemExit("runner state block not found")
s=s.replace(old_state,new_state,1)

css_anchor=""".hk-runner-actions{display:flex;gap:7px}.hk-runner-actions button{flex:1;min-height:34px;font-size:11px}.hk-roadmap"""
css_new=""".hk-runner-actions{display:flex;gap:7px}.hk-runner-actions button{flex:1;min-height:34px;font-size:11px}.hk-runner.buildings-run{margin:0 0 14px;padding:14px 16px;border:1px solid #304057;border-radius:16px;background:#111925;box-shadow:none}.hk-runner.buildings-run .hk-runner-head b{font-size:15px;color:#f2f5fa}.hk-runner.buildings-run .hk-runner-state{padding:4px 8px;border-radius:999px;background:#1d2a3c;color:#cbd7e6;font-size:9px;font-weight:800}.hk-runner.buildings-run .hk-runner-step{margin-top:7px;color:#9fb0c6;font-size:11px}.hk-runner.buildings-run .hk-runner-track{height:7px;margin:10px 0 9px;background:#26364b}.hk-runner.buildings-run .hk-runner-actions{justify-content:flex-end}.hk-runner.buildings-run .hk-runner-actions button{flex:0 0 auto;width:auto;min-width:132px;min-height:36px;padding:9px 16px}.hk-runner.buildings-run .hk-runner-history{border-color:#304057;background:#0c131d}.hk-roadmap"""
if css_anchor not in s:
    raise SystemExit("runner css anchor not found")
s=s.replace(css_anchor,css_new,1)

mobile_anchor="""@media(max-width:760px){.hk-building-controls{grid-template-columns:1fr}.hk-building-stats{grid-template-columns:1fr 1fr}.hk-building-actions{grid-template-columns:1fr}.hk-buildings-head{align-items:flex-start}.hk-buildings-head .hk-secondary{min-width:96px}.hk-building-area{max-width:120px}}"""
mobile_new="""@media(max-width:760px){.hk-building-controls{grid-template-columns:1fr}.hk-building-stats{grid-template-columns:1fr 1fr}.hk-building-actions{grid-template-columns:1fr}.hk-buildings-head{align-items:flex-start}.hk-buildings-head .hk-secondary{min-width:96px}.hk-building-area{max-width:120px}.hk-runner.buildings-run .hk-runner-actions{display:grid;grid-template-columns:1fr 1fr}.hk-runner.buildings-run .hk-runner-actions button{width:100%;min-width:0}}"""
if mobile_anchor not in s:
    raise SystemExit("mobile css anchor not found")
s=s.replace(mobile_anchor,mobile_new,1)

stats_css=".hk-building-stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px;margin-bottom:9px}"
if stats_css not in s:
    raise SystemExit("building stats css not found")
s=s.replace(stats_css,".hk-building-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;margin-bottom:9px}",1)

old_controls="""        '<div class="hk-building-controls">'+
          '<label class="hk-building-field"><span>'+either('Минимум кристаллов','Minimum crystals')+'</span><input id="hk-building-min-crystals" type="number" min="0" step="1" value="'+settings.minCrystals+'"></label>'+
          '<label class="hk-building-field"><span>'+either('В избранное от','Favorite from')+'</span><input id="hk-building-favorite-from" type="number" min="0" step="1" value="'+settings.favoriteFrom+'"></label>'+
          '<label class="hk-building-field"><span>'+either('Тип здания','Building type')+'</span><select id="hk-building-type"><option value="normal" '+(settings.buildingType==='normal'?'selected':'')+'>'+either('Обычные','Normal')+'</option><option value="investment" '+(settings.buildingType==='investment'?'selected':'')+'>'+either('Инвестиционные','Investment')+'</option><option value="all" '+(settings.buildingType==='all'?'selected':'')+'>'+either('Все','All')+'</option></select></label>'+
        '</div>'+
        '<div class="hk-building-actions"><button id="hk-building-plan" class="hk-secondary" '+(buildingCanonBusy?'disabled':'')+'>'+either('Рассчитать кандидатов','Calculate candidates')+'</button><button id="hk-building-run" class="hk-primary" '+(buildingCanonBusy||!plan?.candidates?.length?'disabled':'')+'>'+either('Открыть подходящие','Open eligible')+'</button></div>'+
"""
new_controls="""        '<div class="hk-building-controls">'+
          '<label class="hk-building-field"><span>'+either('Минимум кристаллов','Minimum crystals')+'</span><input id="hk-building-min-crystals" type="number" min="0" step="1" value="'+settings.minCrystals+'"></label>'+
          '<label class="hk-building-field"><span>'+either('В избранное от','Favorite from')+'</span><input id="hk-building-favorite-from" type="number" min="0" step="1" value="'+settings.favoriteFrom+'"></label>'+
          '<label class="hk-building-field"><span>'+either('Тип здания','Building type')+'</span><select id="hk-building-type"><option value="normal" '+(settings.buildingType==='normal'?'selected':'')+'>'+either('Обычные','Normal')+'</option><option value="investment" '+(settings.buildingType==='investment'?'selected':'')+'>'+either('Инвестиционные','Investment')+'</option><option value="all" '+(settings.buildingType==='all'?'selected':'')+'>'+either('Все','All')+'</option></select></label>'+
          '<label class="hk-building-field"><span>'+either('Лимит открытия','Open limit')+'</span><select id="hk-building-open-limit"><option value="1" '+(settings.openLimit===1?'selected':'')+'>1</option><option value="10" '+(settings.openLimit===10?'selected':'')+'>10</option><option value="15" '+(settings.openLimit===15?'selected':'')+'>15</option><option value="20" '+(settings.openLimit===20?'selected':'')+'>20</option><option value="all" '+(settings.openLimit===0?'selected':'')+'>'+either('Все доступные','All available')+'</option></select></label>'+
        '</div>'+
        '<div class="hk-building-actions"><button id="hk-building-plan" class="hk-secondary" '+(buildingCanonBusy?'disabled':'')+'>'+either('Рассчитать кандидатов','Calculate candidates')+'</button><button id="hk-building-run" class="hk-primary" '+(buildingCanonBusy||!plan?.candidates?.length?'disabled':'')+'>'+(settings.openLimit===0?either('Открыть все доступные','Open all available'):either('Открыть до '+settings.openLimit,'Open up to '+settings.openLimit))+'</button></div>'+
"""
if old_controls not in s:
    raise SystemExit("building controls block not found")
s=s.replace(old_controls,new_controls,1)

old_stats="""    const activeValue=capacity.active+(capacity.max===null?'':'/'+capacity.max);
    const planSummary=plan?
      '<div class="hk-cardbox hk-building-plan">'+
        '<div class="hk-building-plan-head"><b>'+either('План открытия','Opening plan')+'</b><span class="hk-muted">'+new Date(plan.at||Date.now()).toLocaleTimeString(locale(),{hour:'2-digit',minute:'2-digit'})+'</span></div>'+
        '<div class="hk-building-stats">'+
          '<div class="hk-building-stat"><span>'+either('Кандидаты','Candidates')+'</span><b>'+plan.candidates.length+'</b></div>'+
          '<div class="hk-building-stat"><span>'+either('Активные','Active')+'</span><b>'+activeValue+'</b></div>'+
          '<div class="hk-building-stat"><span>'+either('Карты районов','Mapped districts')+'</span><b>'+plan.mappedAreas+'/'+plan.ownedAreas+'</b></div>'+
"""
new_stats="""    const activeValue=capacity.active+(capacity.max===null?'':'/'+capacity.max);
    const freeCap=capacity.free===null?plan?.candidates?.length||0:Math.max(0,capacity.free);
    const selectedRunCount=plan?Math.min(plan.candidates.length,freeCap,settings.openLimit===0?Number.MAX_SAFE_INTEGER:settings.openLimit):0;
    const planSummary=plan?
      '<div class="hk-cardbox hk-building-plan">'+
        '<div class="hk-building-plan-head"><b>'+either('План открытия','Opening plan')+'</b><span class="hk-muted">'+new Date(plan.at||Date.now()).toLocaleTimeString(locale(),{hour:'2-digit',minute:'2-digit'})+'</span></div>'+
        '<div class="hk-building-stats">'+
          '<div class="hk-building-stat"><span>'+either('Кандидаты','Candidates')+'</span><b>'+plan.candidates.length+'</b></div>'+
          '<div class="hk-building-stat"><span>'+either('К запуску','To open')+'</span><b>'+selectedRunCount+'</b></div>'+
          '<div class="hk-building-stat"><span>'+either('Активные','Active')+'</span><b>'+activeValue+'</b></div>'+
          '<div class="hk-building-stat"><span>'+either('Карты районов','Mapped districts')+'</span><b>'+plan.mappedAreas+'/'+plan.ownedAreas+'</b></div>'+
"""
if old_stats not in s:
    raise SystemExit("building stats block not found")
s=s.replace(old_stats,new_stats,1)

old_listeners="""    box.querySelector('#hk-building-min-crystals')?.addEventListener('change',saveControls);
    box.querySelector('#hk-building-favorite-from')?.addEventListener('change',saveControls);
    box.querySelector('#hk-building-type')?.addEventListener('change',saveControls);
"""
new_listeners="""    box.querySelector('#hk-building-min-crystals')?.addEventListener('change',saveControls);
    box.querySelector('#hk-building-favorite-from')?.addEventListener('change',saveControls);
    box.querySelector('#hk-building-type')?.addEventListener('change',saveControls);
    box.querySelector('#hk-building-open-limit')?.addEventListener('change',()=>{
      const next=buildingCanonReadSettingsFromDom();
      buildingCanonSaveSettings(next);
      renderBuildings();
    });
"""
if old_listeners not in s:
    raise SystemExit("building listener block not found")
s=s.replace(old_listeners,new_listeners,1)

for marker in [
    "// @version      1.17.17",
    "const BUILD_VERSION = '1.17.17';",
    "core-20260921-r19-buildings-limit-runner",
    "buildings-open-limit-20260921-r1",
    "buildings-runner-ui-20260921-r1",
    "id=\"hk-building-open-limit\"",
    "Открыть до ",
    "Открыть зданий:",
    "box.classList.toggle('buildings-run',buildingsRun)",
    ".hk-runner.buildings-run",
    "maps-shared-runtime-20260921-r7-safe5",
    "explore-e3-single-20260920-r9-runner",
    "AUTH_PASSIVE_SAFETY_R1",
]:
    if marker not in s:
        raise SystemExit(f"post-patch marker missing: {marker}")

PATH.write_text(s,encoding="utf-8")
print("BUILDINGS_LIMIT_RUNNER_R1_PATCH=PASS")
