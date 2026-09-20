from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')

BASE="const HK_PITS_POWER_TABLE_REV = 'pits-power-table-collapsed-20260920-r7';"
MARK="const HK_PITS_PROGRESS_REV = 'pits-battle-progress-20260920-r8';"
if MARK in s:
    raise SystemExit('already applied')
if BASE not in s:
    raise SystemExit('r7 marker missing')
s=s.replace(BASE, BASE+"\n  "+MARK, 1)

anchor="""  function pitCanonRespawnCost(state,chunk=1) {
    const options=Array.isArray(state?.respawn_costs)?state.respawn_costs:[];
    const option=options.find(row=>row?.is_prem===false);
    const quantity=pitCanonCostQuantity(option,HK_PIT_RESTORATION_ITEM_ID,'item');
    return pitCanonWhole(quantity)||Math.max(1,pitCanonWhole(chunk));
  }

"""
if anchor not in s:
    raise SystemExit('respawn helper anchor missing')

helpers="""  function pitCanonRespawnCost(state,chunk=1) {
    const options=Array.isArray(state?.respawn_costs)?state.respawn_costs:[];
    const option=options.find(row=>row?.is_prem===false);
    const quantity=pitCanonCostQuantity(option,HK_PIT_RESTORATION_ITEM_ID,'item');
    return pitCanonWhole(quantity)||Math.max(1,pitCanonWhole(chunk));
  }

  function pitCanonSetBusy(busy) {
    const box=root?.querySelector('#hk-pits-content');
    if(!box)return;
    box.querySelectorAll('[data-pit-canon-enabled],[data-pit-canon-plan],[data-pit-canon-target],[data-pit-canon-paws],[data-pit-canon-autofinish],[data-pit-canon-sniper],[data-pit-canon-sniper-payment],#hk-pits-autofinish-all,#hk-pits-start').forEach(control=>{
      if(!control)return;
      if(busy){
        control.dataset.pitBusyDisabled=control.disabled?'1':'0';
        control.disabled=true;
      }else if(control.dataset.pitBusyDisabled==='0'){
        control.disabled=false;
        delete control.dataset.pitBusyDisabled;
      }else{
        delete control.dataset.pitBusyDisabled;
      }
    });
    box.classList.toggle('hk-pits-busy',!!busy);
  }

  function pitCanonBattleTelemetry(def,level) {
    const type=def?.id;
    const numericLevel=pitCanonWhole(level);
    const exactRow=combinedPitRows(type).find(row=>Number(row?.level)===numericLevel);
    const exactPower=Number(exactRow?.enemy_power||0);
    const enemyPower=exactPower>0?exactPower:Number(predictedPitPower(numericLevel,type)||0);
    const profile=pitForecastProfile(type);
    const playerPower=type==='gang'?0:Number(profile?.playerPower||0);
    const chance=enemyPower>0?pitForecastChance(type,numericLevel,enemyPower):null;
    const parts=[];
    if(enemyPower>0){
      parts.push(exactPower>0
        ? `${either('сила Ямы','Pit power')}: ${Math.round(enemyPower).toLocaleString(locale())}`
        : `${either('прогноз силы Ямы','predicted Pit power')}: ${Math.round(enemyPower).toLocaleString(locale())}`);
    }
    if(playerPower>0)parts.push(`${either('наша сила','our power')}: ${Math.round(playerPower).toLocaleString(locale())}`);
    if(chance!==null)parts.push(`${either('шанс','chance')}: ${pitChanceLabel(chance)}`);
    return {enemyPower,playerPower,chance,text:parts.join(' · ')};
  }

"""
s=s.replace(anchor,helpers,1)

old_start="""    hkRunner.start({title:either('Ямы','Pits'),step:either('Подготовка','Preparing'),total,pausable:true,stoppable:true});
    recordDiagnostic('pits-run-config-snapshot',{pits:configs.map(config=>({id:config.definition?.id,planId:config.planId,steps:config.steps?.length||0,sniper:!!config.sniper,target:config.target}))});
    try{
"""
new_start="""    hkRunner.start({title:either('Ямы','Pits'),step:either('Подготовка','Preparing'),total,pausable:true,stoppable:true});
    pitCanonSetBusy(true);
    log(either('Ямы — запуск выбранного плана','Pits — starting selected plan'),'info');
    recordDiagnostic('pits-run-config-snapshot',{pits:configs.map(config=>({id:config.definition?.id,planId:config.planId,steps:config.steps?.length||0,sniper:!!config.sniper,target:config.target}))});
    try{
"""
if old_start not in s:
    raise SystemExit('runner start anchor missing')
s=s.replace(old_start,new_start,1)

old_launch="""        hkRunner.setStep(`${pitCanonDefinitionName(def)} · ${either('запуск','start')} ×${chunk}`,progress.done,progress.total);
        if(payment==='FREE')await apiJson(api.start,'POST',{mass_multiplier:chunk});else await apiJson(api.pass,'POST',{mass_multiplier:chunk,payment_type:payment});
"""
new_launch="""        hkRunner.setStep(`${pitCanonDefinitionName(def)} · ${either('запуск','start')} ×${chunk}`,progress.done,progress.total);
        log(`${pitCanonDefinitionName(def)} — ${either('запуск раунда','starting round')} ×${chunk} · ${either('оплата','payment')}: ${payment}`,'info');
        if(payment==='FREE')await apiJson(api.start,'POST',{mass_multiplier:chunk});else await apiJson(api.pass,'POST',{mass_multiplier:chunk,payment_type:payment});
"""
if old_launch not in s:
    raise SystemExit('launch anchor missing')
s=s.replace(old_launch,new_launch,1)

old_rest="""          hkRunner.setStep(`${pitCanonDefinitionName(def)} · ${either('восстановление','restoration')} 🐾 ${cost}`,progress.done,progress.total);await apiJson(api.respawn,'POST',{payment_type:'ITEM'});restorationSpent+=cost;
          playerDocument=await hkAuthoritativePlayerRead(`pits:${def.id}:after-respawn`);state=pitRaceSnapshot(def.id,playerDocument);continue;
"""
new_rest="""          hkRunner.setStep(`${pitCanonDefinitionName(def)} · ${either('восстановление','restoration')} 🐾 ${cost}`,progress.done,progress.total);
          log(`${pitCanonDefinitionName(def)} — ${either('восстановление','restoration')}: 🐾 ${cost} · ${either('потрачено скриптом','spent by script')}: ${restorationSpent+cost}/${config.maxRestoration}`,'warn');
          await apiJson(api.respawn,'POST',{payment_type:'ITEM'});restorationSpent+=cost;
          playerDocument=await hkAuthoritativePlayerRead(`pits:${def.id}:after-respawn`);state=pitRaceSnapshot(def.id,playerDocument);
          log(`✓ ${pitCanonDefinitionName(def)} — ${either('восстановлено','restored')} · HP ${pitCanonWhole(state?.health)} · 🐾 ${pitCanonResourceQuantity(playerDocument,HK_PIT_RESTORATION_ITEM_ID,'item')} ${either('осталось','remaining')}`,'ok');
          continue;
"""
if old_rest not in s:
    raise SystemExit('restoration anchor missing')
s=s.replace(old_rest,new_rest,1)

old_battle="""        hkRunner.setStep(`${pitCanonDefinitionName(def)} · ${either('бой','battle')} ${level} → ${level+1}`,progress.done,progress.total);await apiJson(api.battle,'POST');
        playerDocument=await hkAuthoritativePlayerRead(`pits:${def.id}:after-battle`);state=pitRaceSnapshot(def.id,playerDocument);
"""
new_battle="""        const telemetry=pitCanonBattleTelemetry(def,level);
        hkRunner.setStep(`${pitCanonDefinitionName(def)} · ${either('бой','battle')} ${level} → ${level+1} · HP ${pitCanonWhole(state.health)}${telemetry.text?` · ${telemetry.text}`:''}`,progress.done,progress.total);
        log(`${pitCanonDefinitionName(def)} — ${either('бой','battle')} ${level} → ${level+1}${telemetry.text?` · ${telemetry.text}`:''}`,'info');
        const battleResponse=await apiJson(api.battle,'POST');
        playerDocument=await hkAuthoritativePlayerRead(`pits:${def.id}:after-battle`);state=pitRaceSnapshot(def.id,playerDocument);
        const afterLevel=pitCanonWhole(state?.level);
        const won=afterLevel>level||battleResponse?.battle_result?.is_win===true;
        log(`${won?'✓':'✗'} ${pitCanonDefinitionName(def)} — ${won?either('ПРОБИТО','WON'):either('НЕ ПРОБИТО','LOST')} · ${level} → ${level+1} · HP ${pitCanonWhole(state?.health)}${telemetry.chance!==null?` · ${either('шанс','chance')}: ${pitChanceLabel(telemetry.chance)}`:''}`,won?'ok':'warn');
"""
if old_battle not in s:
    raise SystemExit('battle anchor missing')
s=s.replace(old_battle,new_battle,1)

old_finish="""      if(state&&state.is_finish===false&&config.autofinish){hkRunner.setStep(`${pitCanonDefinitionName(def)} · ${either('завершение','finish')}`,progress.done,progress.total);try{await apiJson(api.finish,'POST');}catch(error){if(!pitAlreadyFinishedError(error))throw error;}playerDocument=await hkAuthoritativePlayerRead(`pits:${def.id}:after-finish`);}
"""
new_finish="""      if(state&&state.is_finish===false&&config.autofinish){
        hkRunner.setStep(`${pitCanonDefinitionName(def)} · ${either('завершение','finish')}`,progress.done,progress.total);
        log(`${pitCanonDefinitionName(def)} — ${either('завершение раунда','finishing round')} · ${either('уровень','level')} ${pitCanonWhole(state.level)}`,'info');
        try{await apiJson(api.finish,'POST');}catch(error){if(!pitAlreadyFinishedError(error))throw error;}
        playerDocument=await hkAuthoritativePlayerRead(`pits:${def.id}:after-finish`);
        log(`✓ ${pitCanonDefinitionName(def)} — ${either('раунд завершён','round completed')}`,'ok');
      }
"""
if old_finish not in s:
    raise SystemExit('finish anchor missing')
s=s.replace(old_finish,new_finish,1)

old_catch="""    }catch(error){
      if(error?.name==='AbortError'){hkRunner.reset();log(either('Ямы остановлены пользователем','Pits stopped by user'),'warn');}else{hkRunner.fail(error);log(`${either('Ошибка Ям','Pits error')}: ${error?.message||error}`,'bad');}
      try{playerDocument=await hkAuthoritativePlayerRead('pits:error-reread');pitCanonRender();}catch(_){}
    }
"""
new_catch="""    }catch(error){
      if(error?.name==='AbortError'){hkRunner.reset();log(either('Ямы остановлены пользователем','Pits stopped by user'),'warn');}else{hkRunner.fail(error);log(`${either('Ошибка Ям','Pits error')}: ${error?.message||error}`,'bad');}
      try{playerDocument=await hkAuthoritativePlayerRead('pits:error-reread');pitCanonRender();}catch(_){}
    }finally{
      pitCanonSetBusy(false);
    }
"""
if old_catch not in s:
    raise SystemExit('catch anchor missing')
s=s.replace(old_catch,new_catch,1)

# Slight visual cue while controls are locked.
css_anchor=".hk-pits-cards+.hk-primary{margin-top:12px}"
css_new=".hk-pits-cards+.hk-primary{margin-top:12px}.hk-pits-busy{opacity:.88}.hk-pits-busy .hk-pit-canon-card{filter:saturate(.85)}"
if css_anchor not in s:
    raise SystemExit('pits css anchor missing')
s=s.replace(css_anchor,css_new,1)

for needle in [
    MARK,
    "function pitCanonSetBusy(busy)",
    "function pitCanonBattleTelemetry(def,level)",
    "ПРОБИТО",
    "НЕ ПРОБИТО",
    "pits-battle-progress-20260920-r8",
    "pitCanonSetBusy(true)",
    "pitCanonSetBusy(false)"
]:
    if needle not in s:
        raise SystemExit('missing r8 invariant: '+needle)

p.write_text(s,encoding='utf-8')
print('PITS_PROGRESS_R8_PATCH_OK')
