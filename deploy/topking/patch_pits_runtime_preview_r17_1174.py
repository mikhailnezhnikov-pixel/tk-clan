from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')

BASE="const HK_PITS_REWARD_ONLY_REV = 'pits-reward-only-plan-20260920-r16';"
MARK="const HK_PITS_PREVIEW_REV = 'pits-runtime-preview-20260920-r17';"
if MARK in s: raise SystemExit('already applied')
if BASE not in s: raise SystemExit('r16 marker missing')
s=s.replace(BASE,BASE+"\n  "+MARK,1)

s=s.replace(
"{id:'normal', textKey:'pitNormal', currencyId:'cur_pit_pass', icon:'https://cdn-prod-front-dist.hwgame.cloud/assets/images/ui/pit-icon.png',api:'pit',leaderboardType:'pit_daily_lb',scoreItemId:'item_pit_fake_lb_score'}",
"{id:'normal', textKey:'pitNormal', currencyId:'cur_pit_pass', icon:'https://cdn-prod-front-dist.hwgame.cloud/assets/images/ui/pit-icon.png',api:'pit',previewApi:'pit',leaderboardType:'pit_daily_lb',scoreItemId:'item_pit_fake_lb_score'}",1)
s=s.replace(
"{id:'boss', textKey:'pitBoss', currencyId:'cur_pit_2_pass', icon:'https://cdn-prod-front-dist.hwgame.cloud/assets/images/ui/boss-pit-icon.png',api:'boss_pit',leaderboardType:'pit_2_daily_lb',scoreItemId:'item_pit_2_fake_lb_score'}",
"{id:'boss', textKey:'pitBoss', currencyId:'cur_pit_2_pass', icon:'https://cdn-prod-front-dist.hwgame.cloud/assets/images/ui/boss-pit-icon.png',api:'boss_pit',previewApi:'pit_2',leaderboardType:'pit_2_daily_lb',scoreItemId:'item_pit_2_fake_lb_score'}",1)
s=s.replace(
"{id:'gang', textKey:'pitGang', currencyId:'cur_pit_3_pass', icon:'https://cdn-prod-front-dist.hwgame.cloud/assets/images/ui/pve-pit-icon.png',api:'pit_pve',leaderboardType:'pit_3_daily_lb',leaderboardStatus:'ACTUAL',scoreItemId:'item_pit_3_fake_lb_score'}",
"{id:'gang', textKey:'pitGang', currencyId:'cur_pit_3_pass', icon:'https://cdn-prod-front-dist.hwgame.cloud/assets/images/ui/pve-pit-icon.png',api:'pit_pve',previewApi:'pit_pve',leaderboardType:'pit_3_daily_lb',leaderboardStatus:'ACTUAL',scoreItemId:'item_pit_3_fake_lb_score'}",1)

anchor="  function pitCanonBattleTelemetry(def,level) {\n"
helpers="""  const pitCanonRuntimePreview={normal:null,boss:null,gang:null};
  function pitCanonResetRuntimePreview(){pitCanonRuntimePreview.normal=null;pitCanonRuntimePreview.boss=null;pitCanonRuntimePreview.gang=null;}
  function pitCanonCaptureRuntimePreview(def,data){
    if(!def||!data||typeof data!=='object')return;
    const key=def.id==='normal'?'pit_preview':def.id==='boss'?'pit2_preview':'pit_pve_preview';
    const direct=data?.[key];
    if(direct&&typeof direct==='object')pitCanonRuntimePreview[def.id]=direct;
  }
  function pitCanonFormatGameWinrate(value){
    const number=Number(value);
    if(!Number.isFinite(number))return '—';
    if(number===0)return '0%';
    const precise=number.toFixed(8).replace(/0+$/,'').replace(/\\.$/,'');
    return precise+'%';
  }
  function pitCanonRuntimeWinrateText(def){
    const preview=pitCanonRuntimePreview?.[def?.id];
    if(!preview)return '—';
    if(def?.id==='normal'||def?.id==='boss')return pitCanonFormatGameWinrate(preview?.winrate);
    const rounds=preview?.rounds;
    if(!Array.isArray(rounds)||!rounds.length)return '—';
    return rounds.map(row=>pitCanonFormatGameWinrate(row?.winrate)).join(' · ');
  }
  async function pitCanonLoadRuntimePreview(def){
    try{
      const previewApi=String(def?.previewApi||def?.api||'');
      if(!previewApi)return null;
      const data=await apiJson('/'+previewApi+'/preview','GET');
      pitCanonCaptureRuntimePreview(def,data);
      return data;
    }catch(_){return null}
  }

"""
if anchor not in s: raise SystemExit('telemetry anchor missing')
s=s.replace(anchor,helpers+anchor,1)

old="""    const chance=enemyPower>0?pitForecastChance(type,numericLevel,enemyPower):null;
    const parts=[];
"""
new="""    const chance=enemyPower>0?pitForecastChance(type,numericLevel,enemyPower):null;
    const runtimeWinrate=pitCanonRuntimeWinrateText(def);
    const runtimeKnown=runtimeWinrate!=='—';
    const chanceText=runtimeKnown?runtimeWinrate:(chance!==null?pitChanceLabel(chance):'');
    const parts=[];
"""
if old not in s: raise SystemExit('telemetry chance anchor missing')
s=s.replace(old,new,1)

old="""    if(playerPower>0)parts.push(`${either('наша сила','our power')}: ${Math.round(playerPower).toLocaleString(locale())}`);
    if(chance!==null)parts.push(`${either('шанс','chance')}: ${pitChanceLabel(chance)}`);
    return {enemyPower,playerPower,chance,text:parts.join(' · ')};
"""
new="""    if(playerPower>0)parts.push(`${either('наша сила','our power')}: ${Math.round(playerPower).toLocaleString(locale())}`);
    if(chanceText)parts.push(`${runtimeKnown?either('шанс игры','game winrate'):either('шанс','chance')}: ${chanceText}`);
    return {enemyPower,playerPower,chance,runtimeKnown,runtimeWinrate,chanceText,text:parts.join(' · ')};
"""
old=old.replace('`',chr(96)).replace('§'+chr(123),'$'+chr(123))
new=new.replace('`',chr(96)).replace('§'+chr(123),'$'+chr(123))
if old not in s: raise SystemExit('telemetry return anchor missing')
s=s.replace(old,new,1)

needle="""    pitCanonDecisionBudgetReset();
    pitCanonSetBusy(true);
"""
replace="""    pitCanonDecisionBudgetReset();
    pitCanonResetRuntimePreview();
    pitCanonSetBusy(true);
"""
if needle not in s: raise SystemExit('run reset anchor missing')
s=s.replace(needle,replace,1)

needle=r"""      if(resuming){if(!active)throw new Error(`${pitCanonDefinitionName(def)}: ${either('активная Яма изменилась','active Pit changed')}`);chunk=Math.max(1,pitCanonWhole(active.mass_multiplier ?? active.multiplier));state=active;}
      else{
"""
replace=r"""      if(resuming){
        if(!active)throw new Error(`${pitCanonDefinitionName(def)}: ${either('активная Яма изменилась','active Pit changed')}`);
        chunk=Math.max(1,pitCanonWhole(active.mass_multiplier ?? active.multiplier));state=active;
        pitCanonRuntimePreview[def.id]=null;
        await pitCanonLoadRuntimePreview(def);
      } else{
"""
needle=needle.replace('`',chr(96)).replace('§'+chr(123),'$'+chr(123))
replace=replace.replace('`',chr(96)).replace('§'+chr(123),'$'+chr(123))
if needle not in s: raise SystemExit('resume preview anchor missing')
s=s.replace(needle,replace,1)

needle="""        if(payment==='FREE')await apiJson(api.start,'POST',{mass_multiplier:chunk});else await apiJson(api.pass,'POST',{mass_multiplier:chunk,payment_type:payment});
        spentCrystals+=pitCanonWhole(premCost);spentItems+=pitCanonWhole(itemCost);
"""
replace="""        pitCanonRuntimePreview[def.id]=null;
        const startResponse=payment==='FREE'
          ? await apiJson(api.start,'POST',{mass_multiplier:chunk})
          : await apiJson(api.pass,'POST',{mass_multiplier:chunk,payment_type:payment});
        pitCanonCaptureRuntimePreview(def,startResponse);
        if(pitCanonRuntimeWinrateText(def)==='—')await pitCanonLoadRuntimePreview(def);
        spentCrystals+=pitCanonWhole(premCost);spentItems+=pitCanonWhole(itemCost);
"""
if needle not in s: raise SystemExit('start response anchor missing')
s=s.replace(needle,replace,1)

needle="""          const respawnResponse=await apiJson(api.respawn,'POST',{payment_type:'ITEM'});restorationSpent+=cost;stats.restoration+=cost;
"""
replace="""          const respawnResponse=await apiJson(api.respawn,'POST',{payment_type:'ITEM'});restorationSpent+=cost;stats.restoration+=cost;
          pitCanonCaptureRuntimePreview(def,respawnResponse);
          if(pitCanonRuntimeWinrateText(def)==='—')await pitCanonLoadRuntimePreview(def);
"""
if needle not in s: raise SystemExit('respawn preview anchor missing')
s=s.replace(needle,replace,1)

needle="""        const battleResponse=await apiJson(api.battle,'POST');
        {
"""
replace="""        const battleResponse=await apiJson(api.battle,'POST');
        pitCanonCaptureRuntimePreview(def,battleResponse);
        {
"""
if needle not in s: raise SystemExit('battle capture anchor missing')
s=s.replace(needle,replace,1)

old=r"""        pitCanonRunnerLog(`${won?'✓':'✗'} ${pitCanonDefinitionName(def)} — ${won?either('ПРОБИТО','WON'):either('НЕ ПРОБИТО','LOST')} · ${level} → ${level+1} · HP ${pitCanonWhole(state?.health)}${telemetry.chance!==null?` · ${either('шанс','chance')}: ${pitChanceLabel(telemetry.chance)}`:''}`,won?'ok':'warn');
"""
new=r"""        pitCanonRunnerLog(`${won?'✓':'✗'} ${pitCanonDefinitionName(def)} — ${won?either('ПРОБИТО','WON'):either('НЕ ПРОБИТО','LOST')} · ${level} → ${level+1} · HP ${pitCanonWhole(state?.health)}${telemetry.chanceText?` · ${telemetry.runtimeKnown?either('шанс игры','game winrate'):either('шанс','chance')}: ${telemetry.chanceText}`:''}`,won?'ok':'warn');
"""
old=old.replace('`',chr(96)).replace('§'+chr(123),'$'+chr(123))
new=new.replace('`',chr(96)).replace('§'+chr(123),'$'+chr(123))
if old not in s: raise SystemExit('battle result chance anchor missing')
s=s.replace(old,new,1)

for needle in [
    MARK,
    "previewApi:'pit_2'",
    "function pitCanonLoadRuntimePreview(def)",
    "function pitCanonRuntimeWinrateText(def)",
    "pitCanonCaptureRuntimePreview(def,startResponse)",
    "pitCanonCaptureRuntimePreview(def,battleResponse)",
    "шанс игры"
]:
    if needle not in s: raise SystemExit('missing r17 invariant: '+needle)

p.write_text(s,encoding='utf-8')
print('PITS_RUNTIME_PREVIEW_R17_PATCH_OK')
