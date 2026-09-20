from pathlib import Path

p=Path("/tmp/HamsterKingMobile.user.js")
s=p.read_text()

old_marker="const HK_EXPLORE_CANON_REV='explore-readonly-plan-20260920-r7-area-types';"
new_marker="const HK_EXPLORE_CANON_REV='explore-e3-single-20260920-r8';"
assert s.count(old_marker)==1, s.count(old_marker)
s=s.replace(old_marker,new_marker,1)

# Cost endpoints are reads, not actions. Classify them as such so a cost
# response can never be merged into player state as though it were a mutation.
read_anchor="""    '/player/building',
    '/shop/view',"""
read_repl="""    '/player/building',
    '/player/building/fast_completion/cost',
    '/player/building/fast_remort/cost',
    '/shop/view',"""
assert s.count(read_anchor)==1, s.count(read_anchor)
s=s.replace(read_anchor,read_repl,1)

anchor="""  function explorePrOptions(v){return [['min',either('Минимум сначала','Minimum first')],['max',either('Максимум сначала','Maximum first')],['any',either('Любой порядок','Any order')]].map(r=>'<option value="'+r[0]+'" '+(v===r[0]?'selected':'')+'>'+r[1]+'</option>').join('');}"""
assert s.count(anchor)==1, s.count(anchor)

helpers=r'''
  const EXPLORE_E3_MATERIAL_RE=/^item_(?:beams|nails)_t[1-5]$/;
  const EXPLORE_E3_FACTIONS=new Set(['blue','green','orange','violet','khaki','turquoise','red','brown']);
  const EXPLORE_E3_COUNTERS={
    blue:new Set(['khaki','orange']),red:new Set(['turquoise','brown']),khaki:new Set(['red','green']),turquoise:new Set(['blue','violet']),
    green:new Set(['brown','turquoise']),orange:new Set(['khaki','violet']),violet:new Set(['green','red']),brown:new Set(['blue','orange'])
  };
  let exploreE3Tiers=null,exploreE3ShopLots=null;

  function exploreE3Building(doc){return doc?.building||doc?.data?.building||doc?.data||doc||null;}
  function exploreE3Owned(rows,idKeys){
    const out={};for(const row of (Array.isArray(rows)?rows:[])){let id='';for(const key of idKeys){if(row?.[key]){id=String(row[key]);break;}}if(id)out[id]=Math.max(0,Number(row?.quantity||0));}return out;
  }
  function exploreE3Resources(st=exploreState()){return {currencies:exploreE3Owned(st?.currencies,['currency_id','id']),items:exploreE3Owned(st?.items,['item_id','id'])};}
  function exploreE3Missing(costs,resources){
    for(const [kind,owned] of [['currencies',resources?.currencies||{}],['items',resources?.items||{}]]){
      for(const row of (costs?.[kind]||[])){const id=String(row?.id||row?.currency_id||row?.item_id||''),need=Math.max(0,Number(row?.quantity||0)),have=Math.max(0,Number(owned[id]||0));if(id&&have<need)return {kind,id,have,need};}
    }return null;
  }
  function exploreE3EventsFinished(events){for(const e of (events||[])){if(Number(e?.level||0)<Number(e?.max_level||0))return false;for(const x of (e?.side_events||[]))if(Number(x?.level||0)<Number(x?.max_level||0))return false;}return true;}
  function exploreE3Random(min,max){min=Math.max(0,Number(min||0));max=Math.max(min,Number(max||0));return min===max?min:min+Math.floor(Math.random()*(max-min+1));}
  async function exploreE3Delay(settings,type){
    const ms=type==='battle'?Math.max(0,Number(settings?.battleDelayMs||0)):exploreE3Random(settings?.actionDelayMinMs,settings?.actionDelayMaxMs);
    if(ms>0)await sleep(ms);await hkRunner.waitIfPaused();
  }
  function exploreE3PlayerFactions(st=exploreState()){
    const rows=st?.playerFactions||st?.player_factions||[],out={};
    for(const row of (Array.isArray(rows)?rows:[])){const id=String(row?.id||row?.faction_id||'');if(EXPLORE_E3_FACTIONS.has(id))out[id]=Number(row?.power??row?.overall_power??row?.total_power??0);}
    return out;
  }
  function exploreE3PickFaction(enemy,st=exploreState()){
    let best='',power=-Infinity;for(const id of (EXPLORE_E3_COUNTERS[String(enemy||'')]||[])){const v=Number(exploreE3PlayerFactions(st)[id]);if(Number.isFinite(v)&&v>power){best=id;power=v;}}return best;
  }
  async function exploreE3Detail(buildingId){
    const doc=await apiJson('/player/building?building_id='+encodeURIComponent(buildingId),'POST');buildingStudyCache.set(buildingId,doc);return exploreE3Building(doc);
  }
  async function exploreE3Reconcile(buildingId,reason){
    await exploreReadFreshPlayer(reason);const building=await exploreE3Detail(buildingId);return {state:exploreState(),building};
  }
  async function exploreE3Mutation(path,body,buildingId,reason){
    let data=null,error=null;try{data=await apiJson(path,'POST',body);}catch(e){error=e;}
    let reconciled=null;try{reconciled=await exploreE3Reconcile(buildingId,reason);}catch(e){if(!error)error=e;}
    return {data,error,building:reconciled?.building||exploreE3Building(data),state:reconciled?.state||exploreState()};
  }
  async function exploreE3LoadTiers(){
    if(exploreE3Tiers)return exploreE3Tiers;const data=await growthStaticJson('tiers');const rows=Array.isArray(data)?data:(Array.isArray(data?.tiers)?data.tiers:[]);
    if(!rows.length)throw new Error(either('Не удалось загрузить стоимости тиров','Could not load tier costs'));exploreE3Tiers=rows;return rows;
  }
  async function exploreE3RemortCosts(currentTier){
    const rows=await exploreE3LoadTiers(),target=Number(currentTier)+1,row=rows.find(x=>Number(x?.tier)===target);return row?.costs&&typeof row.costs==='object'?row.costs:null;
  }
  async function exploreE3LoadShopLots(){
    if(exploreE3ShopLots instanceof Map)return exploreE3ShopLots;const doc=await apiJson('/shop/view','GET'),m=new Map();
    for(const lot of (doc?.shop_lots||[])){const content=Array.isArray(lot?.lot_view?.content_view)?lot.lot_view.content_view:[],reward=content.length===1?content[0]:null,id=String(reward?.id||''),qty=Math.max(0,Number(reward?.quantity||lot?.lot_view?.quantity||0));
      if(!EXPLORE_E3_MATERIAL_RE.test(id)||!qty||!lot?.id)continue;const row={id:String(lot.id),quantity:qty,cost:lot.cost||{}};if(!m.has(id))m.set(id,[]);m.get(id).push(row);}
    for(const rows of m.values())rows.sort((a,b)=>a.quantity-b.quantity);exploreE3ShopLots=m;return m;
  }
  async function exploreE3EnsureMaterial(itemId,required){
    required=Math.max(0,Number(required||0));let state=exploreState(),resources=exploreE3Resources(state),owned=Math.max(0,Number(resources.items[itemId]||0));if(owned>=required)return {ok:true};
    const lots=await exploreE3LoadShopLots(),lot=(lots.get(itemId)||[])[0];if(!lot)return {ok:false,reason:either('Материал отсутствует в магазине: ','Material unavailable in shop: ')+itemId};
    for(let guard=0;owned<required&&guard<100;guard++){
      await hkRunner.waitIfPaused();resources=exploreE3Resources(exploreState());const missing=exploreE3Missing(lot.cost,resources);if(missing)return {ok:false,reason:missing.id+': '+missing.have+'/'+missing.need};
      const before=owned,res=await exploreE3Mutation('/shop/buy',{shop_lot_id:lot.id,payment_type:'INTERNAL',lotName:'',lotDescription:''},String(explorePlan?.selected?.[0]?.id||''),'explore:e3-material');
      if(res.error&&!res.state)return {ok:false,reason:res.error?.message||String(res.error)};resources=exploreE3Resources(exploreState());owned=Math.max(0,Number(resources.items[itemId]||0));if(owned<=before)return {ok:false,reason:either('Покупка материала не изменила баланс','Material purchase did not change balance')};
    }
    return {ok:owned>=required,reason:owned>=required?'':either('Лимит покупки материала','Material purchase safety limit')};
  }
  async function exploreE3PrepareCosts(costs,settings){
    if(!costs)return {ok:true};
    if(settings.buyMissingMaterials){for(const row of (costs.items||[])){const id=String(row?.id||'');if(!EXPLORE_E3_MATERIAL_RE.test(id))continue;const r=await exploreE3EnsureMaterial(id,Number(row?.quantity||0));if(!r.ok)return r;}}
    const missing=exploreE3Missing(costs,exploreE3Resources(exploreState()));return missing?{ok:false,reason:missing.id+': '+missing.have+'/'+missing.need}:{ok:true};
  }
  async function exploreE3ManualBattles(building,settings){
    let current=building,stuck=0;const buildingId=String(current?.id||''),enemy=String(current?.enemy?.faction_id||''),faction=exploreE3PickFaction(enemy);
    if(!enemy)return {ok:false,reason:either('Не определена фракция противника','Enemy faction is unknown')};if(!faction)return {ok:false,reason:either('Нет подходящей контр-фракции','No suitable counter faction')};
    for(let round=1;Number(current?.battle_level||0)<Number(current?.max_battle_level||0)&&round<=100;round++){
      await hkRunner.waitIfPaused();const before=Number(current?.battle_level||0);hkRunner.setStep(either('Ручной бой','Manual battle')+' · '+before+'/'+Number(current?.max_battle_level||0),0,1);
      const res=await exploreE3Mutation('/player/battle?building_id='+encodeURIComponent(buildingId)+'&faction_id='+encodeURIComponent(faction),null,buildingId,'explore:e3-manual-battle');current=res.building||current;const after=Number(current?.battle_level||0);
      if(after<=before)stuck++;else stuck=0;if(stuck>=5)return {ok:false,reason:either('5 боёв подряд без прогресса','5 consecutive battles without progress')};await exploreE3Delay(settings,'battle');
    }
    return {ok:Number(current?.battle_level||0)>=Number(current?.max_battle_level||0),building:current,reason:either('Бои не завершены','Battles not completed')};
  }
  async function exploreE3ProcessOne(initial,settings){
    const buildingId=String(initial?.id||'');if(!buildingId)throw new Error(either('Нет ID здания','Missing building ID'));let current=await exploreE3Detail(buildingId);
    if(settings.targetTier===8){
      if(Number(current?.tier||0)>=7)return {status:'completed',building:current};
      hkRunner.setStep(either('Проверка Instant MAX','Checking Instant MAX'),0,1);
      const costDoc=await apiJson('/player/building/fast_remort/cost','POST',{building_id:buildingId}),costData=costDoc?.fast_building_remort_cost||{};
      if((costData.required_constructions||[]).length)return {status:'skipped',reason:either('Нужны обязательные конструкции','Required constructions are missing')};
      const prepared=await exploreE3PrepareCosts(costData.costs||{},settings);if(!prepared.ok)return {status:'resources_exhausted',reason:prepared.reason};
      hkRunner.setStep(either('Instant MAX','Instant MAX'),0,1);const res=await exploreE3Mutation('/player/building/fast_remort',{building_id:buildingId},buildingId,'explore:e3-fast-remort');current=res.building||current;
      if(Number(current?.tier||0)<7)return {status:'failed',reason:(res.error?.message||either('MAX не достигнут','MAX was not reached')),building:current};return {status:'completed',building:current};
    }
    for(let guard=0;guard<100;guard++){
      await hkRunner.waitIfPaused();if(!current)current=await exploreE3Detail(buildingId);const tier=Number(current?.tier||0),atTarget=tier===Number(settings.targetTier);
      if(tier>settings.targetTier||(atTarget&&!settings.exploreTargetTier))return {status:'completed',building:current};
      if(!exploreE3EventsFinished(Array.isArray(current?.events)?current.events:[])){
        if(exploreTierModes(Number(exploreState()?.player?.level||0))[tier]!=='fast')return {status:'skipped',reason:either('На этом тире недоступно быстрое исследование','Fast completion is unavailable at this tier'),building:current};
        hkRunner.setStep(either('Проверка стоимости быстрого исследования','Checking fast-completion cost'),0,1);const costDoc=await apiJson('/player/building/fast_completion/cost','POST',{building_id:buildingId}),costData=costDoc?.fast_building_completion_cost||{};
        if((costData.required_constructions||[]).length)return {status:'skipped',reason:either('Нужны обязательные конструкции','Required constructions are missing'),building:current};
        const prepared=await exploreE3PrepareCosts(costData.costs||{},settings);if(!prepared.ok)return {status:'resources_exhausted',reason:prepared.reason,building:current};
        hkRunner.setStep(either('Быстрое исследование','Fast completion'),0,1);const res=await exploreE3Mutation('/player/building/fast_completion',{building_id:buildingId},buildingId,'explore:e3-fast-completion');current=res.building||current;
        if(res.error&&!exploreE3EventsFinished(current?.events||[]))return {status:'failed',reason:res.error?.message||String(res.error),building:current};await exploreE3Delay(settings,'action');continue;
      }
      if(atTarget&&!settings.exploreTargetBattles)return {status:'completed',building:current};
      if(Number(current?.battle_level||0)<Number(current?.max_battle_level||0)){
        const before=Number(current?.battle_level||0),auto=exploreAutoTier(exploreConsigliere(exploreState()));
        if(tier<=auto){
          hkRunner.setStep(either('Автобой','Auto battle')+' · '+before+'/'+Number(current?.max_battle_level||0),0,1);const res=await exploreE3Mutation('/player/battle/fast',{building_id:buildingId},buildingId,'explore:e3-auto-battle');current=res.building||current;
          if(Number(current?.battle_level||0)>before){await exploreE3Delay(settings,'battle');continue;}
        }
        const manual=await exploreE3ManualBattles(current,settings);if(!manual.ok)return {status:'skipped',reason:manual.reason,building:manual.building||current};current=manual.building;continue;
      }
      if(!exploreE3EventsFinished(current?.events||[])){current=await exploreE3Detail(buildingId);continue;}
      if(atTarget)return {status:'completed',building:current};
      hkRunner.setStep(either('Подготовка следующего тира','Preparing next tier'),0,1);const costs=await exploreE3RemortCosts(tier);if(!costs)return {status:'failed',reason:either('Не найдена стоимость следующего тира','Next-tier cost was not found'),building:current};
      const prepared=await exploreE3PrepareCosts(costs,settings);if(!prepared.ok)return {status:'resources_exhausted',reason:prepared.reason,building:current};
      hkRunner.setStep(either('Переход на следующий тир','Upgrading tier'),0,1);const beforeTier=tier,res=await exploreE3Mutation('/player/building/remort?building_id='+encodeURIComponent(buildingId),null,buildingId,'explore:e3-remort');current=res.building||current;
      if(Number(current?.tier||0)<=beforeTier)return {status:'failed',reason:res.error?.message||either('Тир не повысился','Tier did not increase'),building:current};await exploreE3Delay(settings,'action');
    }
    return {status:'failed',reason:either('Достигнут защитный лимит 100 шагов','100-step safety limit reached'),building:current};
  }
  async function runExploreE3Single(){
    if(!requireLicense()||exploreBusy||hkRunner.running)return;const settings=exploreReadSettings();exploreBusy=true;exploreE3ShopLots=null;renderExplore();
    try{
      explorePlan=await exploreBuildPlan();const total=Number(explorePlan?.selected?.length||0);if(!total){log(either('Нет зданий для запуска','No buildings to run'),'warn');return;}
      const candidate=explorePlan.selected[0],ok=confirm(either('E3: обработать 1 тестовое здание из '+total+'? После успешной проверки включим очередь.','E3: process 1 test building out of '+total+'? The queue will be enabled after a successful check.'));
      if(!ok)return;
      hkRunner.start({title:either('Исследование · E3','Explore · E3'),total:1,step:either('Подготовка','Preparing'),pausable:true,stoppable:true});
      const result=await exploreE3ProcessOne(candidate,settings);
      await exploreE3Reconcile(String(candidate.id||''),'explore:e3-final');
      if(result.status==='completed'){hkRunner.advance(either('Здание завершено','Building completed'));hkRunner.note(either('Тестовое здание успешно обработано','Test building processed successfully'),'ok');hkRunner.finish(either('E3 завершён','E3 completed'));log(either('E3: одно здание успешно обработано','E3: one building processed successfully'),'ok');}
      else{const msg=(result.reason||result.status);hkRunner.note(msg,result.status==='skipped'||result.status==='resources_exhausted'?'warn':'bad');hkRunner.fail(new Error(msg));log(either('E3 остановлен: ','E3 stopped: ')+msg,'warn');}
      exploreMeta=await exploreLoadMeta(true,exploreState());explorePlan=null;
    }catch(e){if(e?.name==='AbortError'){hkRunner.reset();log(either('E3 остановлен пользователем','E3 stopped by user'),'warn');}else{hkRunner.fail(e);log(either('Ошибка E3: ','E3 error: ')+(e?.message||e),'bad');}}
    finally{exploreBusy=false;renderExplore();}
  }
'''
s=s.replace(anchor,helpers+chr(10)+anchor,1)

# Remove per-building cards from the plan and keep only totals/warnings.
old_rows="""    const rows=(p?.selected||[]).slice(0,20).map((r,i)=>'<div class="hk-card"><div class="hk-business-info"><b>'+(i+1)+'. '+escapeHtml(r.id)+'</b><small>'+escapeHtml(r.areaId||either('район неизвестен','district unknown'))+' · '+exploreTierLabel(r.tier)+' · '+either('ур.','Lv')+' '+Number(r.level||0)+' · '+either('бой','battle')+' '+Number(r.battle_level||0)+'/'+Number(r.max_battle_level||0)+' · '+either('события','events')+' '+(r.targetRemaining!=null?(r.targetRemaining+'/'+r.targetTotal):(r.totalEvents==null?'?':r.totalEvents))+(r.isInvest===true?' · ◆ '+either('инвест','investment'):r.isInvest===false?' · '+either('обычное','normal'):'')+'</small></div><strong>→ '+exploreTierLabel(s.targetTier)+'</strong></div>').join('');
"""
assert s.count(old_rows)==1, s.count(old_rows)
s=s.replace(old_rows,"",1)

old_plan_start="""    const planHtml=p?'<div class="hk-cardbox"><b>'+either('Read-only план','Read-only plan')+'</b><p class="hk-muted">'+either('После фильтров','After filters')+': '+p.filteredCount+' · '+either('кандидатов','candidates')+': '+p.candidates.length+' · '+either('к обработке','to process')+': '+p.selected.length+'</p>'+"""
new_plan_start="""    const planHtml=p?'<div class="hk-cardbox"><b>'+either('План','Plan')+'</b><p><strong>'+either('Будет обработано зданий: ','Buildings to process: ')+p.selected.length+'</strong></p><p class="hk-muted">'+either('После фильтров','After filters')+': '+p.filteredCount+' · '+either('кандидатов','candidates')+': '+p.candidates.length+'</p>'+"""
assert s.count(old_plan_start)==1, s.count(old_plan_start)
s=s.replace(old_plan_start,new_plan_start,1)

old_tail="""      (p.meta?.unmapped?'<p class="hk-muted">⚠ '+either('Без района','Without district')+': '+p.meta.unmapped+'</p>':'')+(p.meta?.unknownType?'<p class="hk-muted">⚠ '+either('Тип неизвестен','Unknown type')+': '+p.meta.unknownType+'</p>':'')+
      '<div class="hk-cards">'+(rows||'<p class="hk-muted">'+either('Подходящих зданий нет.','No eligible buildings.')+'</p>')+'</div>'+(p.selected.length>20?'<p class="hk-muted">… +'+(p.selected.length-20)+'</p>':'')+'</div>':"""
new_tail="""      (p.meta?.unmapped?'<p class="hk-muted">⚠ '+either('Без района','Without district')+': '+p.meta.unmapped+'</p>':'')+(p.meta?.unknownType?'<p class="hk-muted">⚠ '+either('Тип неизвестен','Unknown type')+': '+p.meta.unknownType+'</p>':'')+'</div>':"""
assert s.count(old_tail)==1, s.count(old_tail)
s=s.replace(old_tail,new_tail,1)

old_buttons="""        '<div class="hk-ex-actions"><button id="hk-ex-plan" class="hk-primary" '+(exploreBusy?'disabled':'')+'>'+(exploreBusy?either('Считаю…','Calculating…'):either('Рассчитать план','Calculate plan'))+'</button><button class="hk-secondary" disabled>'+either('Запуск появится на E3','Run becomes available in E3')+'</button><span id="hk-ex-dirty" class="hk-muted hk-ex-dirty"></span></div>'+"""
new_buttons="""        '<div class="hk-ex-actions"><button id="hk-ex-plan" class="hk-primary" '+(exploreBusy?'disabled':'')+'>'+(exploreBusy?either('Считаю…','Calculating…'):either('Рассчитать план','Calculate plan'))+'</button><button id="hk-ex-run-one" class="hk-secondary" '+(exploreBusy||!p?.selected?.length?'disabled':'')+'>'+either('Запустить тест E3 · 1 здание','Run E3 test · 1 building')+'</button><span id="hk-ex-dirty" class="hk-muted hk-ex-dirty"></span></div>'+"""
assert s.count(old_buttons)==1, s.count(old_buttons)
s=s.replace(old_buttons,new_buttons,1)

event_anchor="""    box.querySelector('#hk-ex-plan')?.addEventListener('click',()=>{exploreReadSettings();explorePlan=null;void explorePreparePlan();});"""
event_repl=event_anchor+"""
    box.querySelector('#hk-ex-run-one')?.addEventListener('click',()=>void runExploreE3Single());"""
assert s.count(event_anchor)==1, s.count(event_anchor)
s=s.replace(event_anchor,event_repl,1)

# Scope checks.
a=s.index("  const HK_EXPLORE_CANON_REV=");b=s.index("  async function acceptBuildingStudy(",a);block=s[a:b]
assert "explore-e3-single-20260920-r8" in block
assert "runExploreE3Single" in block and "runExploreE3Single());" in block
assert "Buildings to process" in block
assert "hk-ex-run-one" in block
assert "/player/building/fast_completion" in block
assert "/player/battle/fast" in block
assert "/player/building/remort?" in block
assert "/player/building/fast_remort" in block
assert "/shop/buy" in block
assert "const HK_MAP_READ_CONCURRENCY = 5;" in s
p.write_text(s)
