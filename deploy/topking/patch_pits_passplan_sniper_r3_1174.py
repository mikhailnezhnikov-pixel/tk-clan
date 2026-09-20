from pathlib import Path

TARGET=Path("/tmp/HamsterKingMobile.user.js")
CORE_MARKER="const HK_PITS_CANON_REV = 'pits-canon-core-20260920-r1';"
UI_MARKER="const HK_PITS_UI_REV = 'pits-ui-align-20260920-r2';"
NEW_MARKER="const HK_PITS_SNIPER_REV = 'pits-passplan-sniper-20260920-r3';"

def require(text, needle, label):
    if needle not in text:
        raise SystemExit(f"missing {label}: {needle}")

def replace_block(text, start_needle, end_needle, replacement, label):
    start=text.find(start_needle)
    if start<0:
        raise SystemExit(f"missing start for {label}")
    end=text.find(end_needle,start+len(start_needle))
    if end<0:
        raise SystemExit(f"missing end for {label}")
    return text[:start]+replacement+text[end:]

s=TARGET.read_text(encoding="utf-8")
require(s,CORE_MARKER,"Core r1")
require(s,UI_MARKER,"UI r2")
if NEW_MARKER in s:
    print("PITS_PASSPLAN_SNIPER_R3_ALREADY_APPLIED")
    raise SystemExit(0)

s=s.replace(UI_MARKER,UI_MARKER+"\n  "+NEW_MARKER,1)

target_helpers=r'''  function pitCanonTargetChoices(state) {
    const current=Math.max(1,pitCanonWhole(state?.level ?? state?.min_pit_level));
    const first=Math.ceil(current/5)*5;
    return [{id:'any',level:0},...Array.from({length:6},(_,index)=>({id:`minimum:${first+index*5}`,level:first+index*5}))];
  }

  function pitCanonSniperTarget(state) {
    const current=Math.max(1,pitCanonWhole(state?.level ?? state?.min_pit_level));
    return (Math.floor(current/5)*5)+15;
  }

  function pitCanonActiveState(typeId,documentValue=playerDocument) {
    const state=pitRaceSnapshot(typeId,documentValue);
    return state&&state.is_finish===false?state:null;
  }

  function pitCanonRowRunnable(row) {
    if(!row)return false;
    if(row.active)return !!row.state;
    if(row.sniper){
      if(row.sniperPayment==='FREE')return pitCanonWhole(row.available)>0;
      if(row.sniperPayment==='ITEM')return row.sniperItemCost!==null&&pitCanonWhole(row.itemPasses)>=pitCanonWhole(row.sniperItemCost);
      return row.sniperPayment==='PREM'&&row.sniperCrystalCost!==null;
    }
    const plan=row.plans?.find(x=>x.id===row.planId);
    if(!plan)return false;
    if(plan.paymentMode==='ITEM')return plan.itemCost!==null&&pitCanonWhole(row.itemPasses)>=pitCanonWhole(plan.itemCost);
    return true;
  }

'''
s=replace_block(s,"  function pitCanonTargetChoices(state) {","  function pitCanonStored() {",target_helpers,"target/sniper helpers")

build_rows=r'''  function pitCanonBuildRows(documentValue=playerDocument) {
    const saved=pitCanonStored();
    const itemPasses=pitCanonResourceQuantity(documentValue,HK_PIT_PASS_ITEM_ID,'item');
    const paws=pitCanonResourceQuantity(documentValue,HK_PIT_RESTORATION_ITEM_ID,'item');
    return HK_PITS_CANON_DEFINITIONS.map(def=>{
      const state=pitRaceSnapshot(def.id,documentValue);
      const activeState=pitCanonActiveState(def.id,documentValue);
      const active=!!activeState;
      const available=pitCanonResourceQuantity(documentValue,def.currencyId,'currency');
      const maximum=Math.max(available,pitCanonCurrencyMax(documentValue,def.currencyId));
      const plans=active?[]:pitCanonPlans(state,available,itemPasses);
      const old=saved.pits?.[def.id]||{};
      const selectedPlan=plans.find(row=>row.id===String(old.planId||''))||plans.find(row=>row.kind==='exact')||plans.find(row=>row.affordable)||plans[0]||null;
      const targets=pitCanonTargetChoices(state);
      const savedTarget=String(old.targetId||'any');
      const target=targets.find(row=>row.id===savedTarget)||targets[0];
      const recommendedSniperTarget=pitCanonSniperTarget(state);
      const sniperTargets=targets.filter(option=>pitCanonWhole(option.level)>=recommendedSniperTarget);
      const activeBatch=Math.max(1,pitCanonWhole(activeState?.mass_multiplier ?? activeState?.multiplier)||1);
      const sniper=active?(activeBatch===1&&!!old.sniper):!!old.sniper;
      const sniperCrystalCost=state?pitCanonDirectPassCost(state,1,'PREM'):null;
      const sniperItemCost=state?pitCanonDirectPassCost(state,1,'ITEM'):null;
      let sniperPayment=String(old.sniperPayment||'');
      if(!['FREE','PREM','ITEM'].includes(sniperPayment))sniperPayment=available>0?'FREE':(sniperCrystalCost!==null?'PREM':'ITEM');
      if(sniperPayment==='FREE'&&available<=0)sniperPayment=sniperCrystalCost!==null?'PREM':'ITEM';
      if(sniperPayment==='PREM'&&sniperCrystalCost===null)sniperPayment=available>0?'FREE':'ITEM';
      if(sniperPayment==='ITEM'&&sniperItemCost===null)sniperPayment=available>0?'FREE':'PREM';
      const savedSniperTarget=pitCanonWhole(old.sniperTarget);
      const sniperTarget=sniperTargets.some(option=>option.level===savedSniperTarget)?savedSniperTarget:recommendedSniperTarget;
      const row={definition:def,state,activeState,active,available,maximum,itemPasses,paws,plans,targets,sniperTargets,
        enabled:false,planId:selectedPlan?.id||'',targetId:target?.id||'any',
        maxRestoration:Math.min(paws,pitCanonWhole(old.maxRestoration)),autofinish:!!old.autofinish,
        sniper,sniperPayment,sniperTarget,recommendedSniperTarget,sniperCrystalCost,sniperItemCost};
      row.enabled=!!old.enabled&&pitCanonRowRunnable(row);
      return row;
    });
  }

'''
s=replace_block(s,"  function pitCanonBuildRows(documentValue=playerDocument) {","  function pitCanonPlanLabel(plan) {",build_rows,"build rows")

save_dom=r'''  function pitCanonSaveDom() {
    const box=root?.querySelector('#hk-pits-content');
    if(!box)return;
    const oldStored=pitCanonStored(),pits={};
    for(const def of HK_PITS_CANON_DEFINITIONS){
      const old=oldStored.pits?.[def.id]||{};
      const sniper=!!box.querySelector(`[data-pit-canon-sniper="${def.id}"]`)?.checked;
      const active=!!pitCanonActiveState(def.id,playerDocument);
      const planValue=String(box.querySelector(`[data-pit-canon-plan="${def.id}"]`)?.value||'');
      const targetValue=String(box.querySelector(`[data-pit-canon-target="${def.id}"]`)?.value||'any');
      const sniperLevel=/^minimum:(\d+)$/.test(targetValue)?pitCanonWhole(targetValue.split(':')[1]):pitCanonWhole(old.sniperTarget);
      pits[def.id]={
        enabled:!!box.querySelector(`[data-pit-canon-enabled="${def.id}"]`)?.checked,
        planId:sniper&&!active?String(old.planId||''):String(planValue||old.planId||''),
        targetId:sniper&&!active?String(old.targetId||'any'):targetValue,
        maxRestoration:pitCanonWhole(box.querySelector(`[data-pit-canon-paws="${def.id}"]`)?.value??old.maxRestoration),
        autofinish:!!box.querySelector(`[data-pit-canon-autofinish="${def.id}"]`)?.checked,
        sniper,
        sniperPayment:String(box.querySelector(`[data-pit-canon-sniper-payment="${def.id}"]`)?.value||old.sniperPayment||''),
        sniperTarget:sniper&&!active?sniperLevel:pitCanonWhole(old.sniperTarget)
      };
    }
    save({pitsCanon:{pits}});
  }

'''
s=replace_block(s,"  function pitCanonSaveDom() {","  function pitCanonRender() {",save_dom,"save dom")

render=r'''  function pitCanonRender() {
    const box=root?.querySelector('#hk-pits-content');
    if(!box)return;
    const rows=pitCanonBuildRows();
    const paws=pitCanonResourceQuantity(playerDocument,HK_PIT_RESTORATION_ITEM_ID,'item');
    const itemPasses=pitCanonResourceQuantity(playerDocument,HK_PIT_PASS_ITEM_ID,'item');
    const crystals=pitCanonResourceQuantity(playerDocument,'cur_prem','currency');
    const allAutofinish=rows.length>0&&rows.every(row=>row.autofinish);
    box.innerHTML=`
      <div class="hk-pits-summary">
        <div><small>${either('Лапы восстановления','Restoration Paws')}</small><b>🐾 ${paws.toLocaleString(locale())}</b></div>
        <div><small>${either('Пропуски Ямы','Pit Passes')}</small><b>🎟 ${itemPasses.toLocaleString(locale())}</b></div>
        <div><small>${either('Кристаллы','Crystals')}</small><b>💎 ${crystals.toLocaleString(locale())}</b></div>
      </div>
      <div class="hk-pits-toolbar"><button id="hk-pits-refresh" class="hk-secondary">${either('Обновить данные','Refresh live data')}</button><label class="hk-pit-canon-global"><input id="hk-pits-autofinish-all" type="checkbox" ${allAutofinish?'checked':''}><span>${either('Автозавершение всех Ям','Auto-finish all Pits')}</span></label></div>
      <div class="hk-pits-cards">${rows.map(row=>{
        const def=row.definition,currentLevel=pitCanonWhole(row.state?.level ?? row.state?.min_pit_level),health=row.activeState?pitCanonWhole(row.activeState.health):null;
        const activeBatch=row.active?Math.max(1,pitCanonWhole(row.activeState?.mass_multiplier ?? row.activeState?.multiplier)||1):0;
        const runnable=pitCanonRowRunnable(row),standaloneSniper=row.sniper&&!row.active;
        const planOptions=standaloneSniper
          ? `<option value="sniper-1" selected>×1</option>`
          : row.active
            ? `<option value="active">${either('Продолжить активную Яму','Continue active Pit')} ×${activeBatch||1}</option>`
            : row.plans.map(plan=>`<option value="${escapeHtml(plan.id)}" ${plan.id===row.planId?'selected':''} ${plan.paymentMode==='ITEM'&&!plan.affordable?'disabled':''}>${escapeHtml(pitCanonPlanLabel(plan))}</option>`).join('');
        const targetRows=standaloneSniper?row.sniperTargets:row.targets;
        const targetOptions=targetRows.map(target=>`<option value="${escapeHtml(target.id)}" ${standaloneSniper?(target.level===row.sniperTarget?'selected':''):(target.id===row.targetId?'selected':'')}>${target.level?`≥ ${target.level}`:either('Неважно — идти как можно дальше','Go as far as possible')}${standaloneSniper&&target.level===row.recommendedSniperTarget?` — ${either('Рекомендуется','Recommended')}`:''}</option>`).join('');
        const paymentOptions=`<option value="FREE" ${row.sniperPayment==='FREE'?'selected':''} ${row.available>0?'':'disabled'}>${either('Бесплатный пропуск','Free pass')}</option><option value="PREM" ${row.sniperPayment==='PREM'?'selected':''} ${row.sniperCrystalCost===null?'disabled':''}>${either('Кристаллы','Crystals')} — 💎 ${pitCanonWhole(row.sniperCrystalCost)}</option><option value="ITEM" ${row.sniperPayment==='ITEM'?'selected':''} ${row.sniperItemCost===null||itemPasses<pitCanonWhole(row.sniperItemCost)?'disabled':''}>${either('Пропуск Ямы','Pit Pass')} — 🎟 ${pitCanonWhole(row.sniperItemCost)}</option>`;
        return `<section class="hk-pit-canon-card ${row.enabled?'selected':''}"><div class="hk-pit-canon-head"><img src="${escapeHtml(def.icon)}" alt=""><div><b>${escapeHtml(pitCanonDefinitionName(def))}</b><small>${row.active?either(`Активна · пакет ×${activeBatch||1}${health===null?'':` · HP ${health}`}`,`Active · batch ×${activeBatch||1}${health===null?'':` · HP ${health}`}`):either('Готова к запуску','Ready')}</small></div><label><input type="checkbox" data-pit-canon-enabled="${def.id}" ${row.enabled?'checked':''} ${runnable?'':'disabled'}><span>${either('Запустить','Run')}</span></label></div><div class="hk-pit-canon-meta"><span>${either('Доступно','Available')}: <b>${row.available.toLocaleString(locale())}</b>${row.maximum?` / ${row.maximum.toLocaleString(locale())}`:''}</span><span>${either('Уровень','Level')}: <b>${currentLevel||'—'}</b></span></div><div class="hk-pit-canon-grid"><label><span>${either('План пропусков','Pass plan')}</span><select data-pit-canon-plan="${def.id}" ${row.active||row.sniper?'disabled':''}>${planOptions}</select></label><label class="hk-pit-canon-check"><span>${either('Режим снайпера','Sniper mode')}</span><input data-pit-canon-sniper="${def.id}" type="checkbox" ${row.sniper?'checked':''} ${row.active&&activeBatch!==1?'disabled':''}></label>${standaloneSniper?`<label><span>${either('Оплата пропуска','Pass payment')}</span><select data-pit-canon-sniper-payment="${def.id}">${paymentOptions}</select></label>`:''}<label><span>${either('Целевой уровень','Target level')}</span><select data-pit-canon-target="${def.id}">${targetOptions}</select></label><label><span>${either('Макс. Лап восстановления на раунд','Max Restoration Paws per round')}</span><input data-pit-canon-paws="${def.id}" type="number" min="0" max="${paws}" value="${row.maxRestoration}"></label><label class="hk-pit-canon-check"><span>${either('Автозавершение Ямы','Auto-finish Pit')}</span><input data-pit-canon-autofinish="${def.id}" type="checkbox" ${row.autofinish?'checked':''}></label></div></section>`;
      }).join('')}</div><button id="hk-pits-start" class="hk-primary">${either('Запустить выбранные Ямы','Start selected Pits')}</button><section id="hk-pit-forecast" class="hk-pit-forecast"></section>`;
    box.querySelector('#hk-pits-refresh').onclick=()=>refreshModuleLive('pit',{force:true});
    box.querySelector('#hk-pits-autofinish-all').onchange=event=>{box.querySelectorAll('[data-pit-canon-autofinish]').forEach(input=>{input.checked=event.target.checked;});pitCanonSaveDom();pitCanonRender();};
    box.querySelectorAll('[data-pit-canon-enabled],[data-pit-canon-plan],[data-pit-canon-target],[data-pit-canon-paws],[data-pit-canon-autofinish],[data-pit-canon-sniper],[data-pit-canon-sniper-payment]').forEach(input=>{input.onchange=()=>{pitCanonSaveDom();pitCanonRender();};});
    box.querySelector('#hk-pits-start').onclick=runPitsCanonical;
    renderPitForecast();
  }

''';
s=replace_block(s,"  function pitCanonRender() {","  function pitCanonReadRunConfigs() {",render,"render")

read_configs=r'''  function pitCanonReadRunConfigs() {
    pitCanonSaveDom();
    const rows=pitCanonBuildRows();
    return rows.filter(row=>row.enabled).map(row=>{
      const standaloneSniper=row.sniper&&!row.active;
      const target=standaloneSniper
        ? {id:`minimum:${pitCanonWhole(row.sniperTarget)}`,level:pitCanonWhole(row.sniperTarget)}
        : (row.targets.find(x=>x.id===row.targetId)||row.targets[0]);
      if(row.active){
        const chunk=Math.max(1,pitCanonWhole(row.activeState?.mass_multiplier ?? row.activeState?.multiplier));
        return {definition:row.definition,planId:'active',steps:[{chunk,payment:'ACTIVE'}],target:pitCanonWhole(target?.level),maxRestoration:row.maxRestoration,autofinish:row.autofinish,resume:true,crystalBudget:0,itemPassBudget:0,sniper:!!row.sniper,sniperPayment:'ACTIVE'};
      }
      if(row.sniper){
        if(!pitCanonRowRunnable(row))return null;
        return {definition:row.definition,planId:'sniper-1',steps:[{chunk:1,payment:row.sniperPayment||'FREE'}],target:pitCanonWhole(row.sniperTarget),maxRestoration:row.maxRestoration,autofinish:row.autofinish,resume:false,crystalBudget:row.sniperPayment==='PREM'?pitCanonWhole(row.sniperCrystalCost):0,itemPassBudget:row.sniperPayment==='ITEM'?pitCanonWhole(row.sniperItemCost):0,sniper:true,sniperPayment:row.sniperPayment};
      }
      const plan=row.plans.find(x=>x.id===row.planId);if(!plan)return null;
      const chunks=row.autofinish?[...plan.chunks]:plan.chunks.slice(0,1);
      return {definition:row.definition,planId:plan.id,steps:chunks.map(chunk=>({chunk,payment:plan.paymentMode})),target:pitCanonWhole(target?.level),maxRestoration:row.maxRestoration,autofinish:row.autofinish,resume:false,crystalBudget:pitCanonWhole(plan.crystalCost),itemPassBudget:pitCanonWhole(plan.itemCost),sniper:false,sniperPayment:''};
    }).filter(config=>config?.steps?.length);
  }

'''
s=replace_block(s,"  function pitCanonReadRunConfigs() {","  async function pitCanonRunOne(config,progress) {",read_configs,"read configs")

run_start=s.find("  async function pitCanonRunOne(config,progress) {")
run_end=s.find("  async function runPitsCanonical() {",run_start)
if run_start<0 or run_end<0:
    raise SystemExit("pitCanonRunOne anchors missing")
run=s[run_start:run_end].replace("pitRaceState(def.id,playerDocument)","pitCanonActiveState(def.id,playerDocument)")
s=s[:run_start]+run+s[run_end:]

for needle in [
    NEW_MARKER,
    "function pitCanonSniperTarget(state)",
    "function pitCanonActiveState(typeId,documentValue=playerDocument)",
    'data-pit-canon-sniper="',
    'data-pit-canon-sniper-payment="',
    "planId:'sniper-1'",
    "pitCanonActiveState(def.id,playerDocument)"
]:
    require(s,needle,"r3 invariant")

TARGET.write_text(s,encoding="utf-8")
print("PITS_PASSPLAN_SNIPER_R3_PATCH_OK")
