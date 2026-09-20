from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')

BASE="const HK_PITS_DECISION_REV = 'pits-restoration-decision-20260920-r11';"
MARK="const HK_PITS_REWARD_REV = 'pits-reward-planner-core-20260920-r12';"
if MARK in s:
    raise SystemExit('already applied')
if BASE not in s:
    raise SystemExit('r11 marker missing')
s=s.replace(BASE,BASE+"\n  "+MARK,1)

old_defs="""const HK_PITS_CANON_DEFINITIONS = [
    {id:'normal', textKey:'pitNormal', currencyId:'cur_pit_pass', icon:'https://cdn-prod-front-dist.hwgame.cloud/assets/images/ui/pit-icon.png'},
    {id:'boss', textKey:'pitBoss', currencyId:'cur_pit_2_pass', icon:'https://cdn-prod-front-dist.hwgame.cloud/assets/images/ui/boss-pit-icon.png'},
    {id:'gang', textKey:'pitGang', currencyId:'cur_pit_3_pass', icon:'https://cdn-prod-front-dist.hwgame.cloud/assets/images/ui/pve-pit-icon.png'}
  ];
  const HK_PITS_CANON_BATCHES = [50,20,10,5,1];
  const HK_PIT_PASS_ITEM_ID = 'item_pit_pass_ticket';
  const HK_PIT_RESTORATION_ITEM_ID = 'item_pit_health_ticket';
"""
new_defs="""const HK_PITS_CANON_DEFINITIONS = [
    {id:'normal', textKey:'pitNormal', currencyId:'cur_pit_pass', icon:'https://cdn-prod-front-dist.hwgame.cloud/assets/images/ui/pit-icon.png',api:'pit',leaderboardType:'pit_daily_lb',scoreItemId:'item_pit_fake_lb_score'},
    {id:'boss', textKey:'pitBoss', currencyId:'cur_pit_2_pass', icon:'https://cdn-prod-front-dist.hwgame.cloud/assets/images/ui/boss-pit-icon.png',api:'boss_pit',leaderboardType:'pit_2_daily_lb',scoreItemId:'item_pit_2_fake_lb_score'},
    {id:'gang', textKey:'pitGang', currencyId:'cur_pit_3_pass', icon:'https://cdn-prod-front-dist.hwgame.cloud/assets/images/ui/pve-pit-icon.png',api:'pit_pve',leaderboardType:'pit_3_daily_lb',leaderboardStatus:'ACTUAL',scoreItemId:'item_pit_3_fake_lb_score'}
  ];
  const HK_PITS_CANON_BATCHES = [50,20,10,5,1];
  const HK_PIT_PASS_ITEM_ID = 'item_pit_pass_ticket';
  const HK_PIT_RESTORATION_ITEM_ID = 'item_pit_health_ticket';
  const HK_PIT_LOOTBOX_ITEM_ID = 'item_pit_lootbox';
  const HK_PIT_LOOTBOX_OPEN_BATCH = 100;
  const HK_PIT_LOOTBOX_EXPECTED_PASSES = 2;
  const pitCanonRewardLive={views:{},leaderboards:{},at:0};
"""
if old_defs not in s:
    raise SystemExit('definitions anchor missing')
s=s.replace(old_defs,new_defs,1)

anchor="  function pitCanonPlans(state,available,itemPasses) {\n"
helpers=r"""  async function pitCanonLoadRewardLive(){
    const views={},leaderboards={};
    await Promise.all(HK_PITS_CANON_DEFINITIONS.map(async def=>{
      try{views[def.id]=await apiJson('/'+def.api+'/view','GET');}catch(_){views[def.id]=null;}
      try{
        const payload={leaderboard_type:def.leaderboardType};
        if(def.leaderboardStatus)payload.leaderboard_status=def.leaderboardStatus;
        leaderboards[def.id]=await apiJson('/leaderboard','POST',payload);
      }catch(_){leaderboards[def.id]=null;}
    }));
    pitCanonRewardLive.views=views;
    pitCanonRewardLive.leaderboards=leaderboards;
    pitCanonRewardLive.at=Date.now();
    recordDiagnostic('pits-reward-live',{views:Object.fromEntries(Object.entries(views).map(([k,v])=>[k,!!v])),leaderboards:Object.fromEntries(Object.entries(leaderboards).map(([k,v])=>[k,!!v]))});
    return pitCanonRewardLive;
  }

  function pitCanonRewardItemMap(view,itemId){
    const result=new Map(),target=String(itemId||'');
    for(const level of view?.levels||[]){
      const item=(level?.reward_view?.reward?.items||[]).find(row=>String(row?.id||'')===target);
      if(item)result.set(pitCanonWhole(level.level),pitCanonWhole(item.count));
    }
    return result;
  }

  function pitCanonRewardTiers(leaderboard){
    return (leaderboard?.score_rewards||[])
      .filter(row=>pitCanonWhole(row?.min_score)>=500000)
      .map(row=>({minScore:pitCanonWhole(row.min_score),maxScore:row.max_score==null?null:pitCanonWhole(row.max_score),rewardView:row.reward_view||{}}))
      .sort((a,b)=>a.minScore-b.minScore);
  }

  function pitCanonEpochMs(value){
    const n=Number(value||0);
    if(!Number.isFinite(n)||n<=0)return 0;
    return n<1e12?Math.floor(n*1000):Math.floor(n);
  }

  function pitCanonTournamentEndTime(leaderboard){
    const direct=pitCanonEpochMs(leaderboard?.end_time);
    if(direct>0)return direct;
    const timer=Number(leaderboard?.end_timer||0),stamp=pitCanonEpochMs(leaderboard?.timestamp);
    return timer>0&&stamp>0?Math.floor(stamp+(timer*1000)):0;
  }

  function pitCanonFutureDailyRefreshCount(endTime,now=Date.now()){
    const end=Number(endTime)||0;
    if(end<=now)return 0;
    const day=86400000,resetOffset=12*60*60*1000;
    let next=(Math.floor(now/day)*day)+resetOffset;
    if(next<=now)next+=day;
    if(next>=end)return 0;
    return Math.floor((end-1-next)/day)+1;
  }

  function pitCanonRewardPointsForTarget(row,targetLevel){
    const target=pitCanonWhole(targetLevel);
    if(!row?.scoreMap?.size||target<=0)return {known:false,points:0};
    let points=0;
    for(let level=0;level<target;level++){
      if(!row.scoreMap.has(level))return {known:false,points:0};
      points+=pitCanonWhole(row.scoreMap.get(level));
    }
    return {known:true,points};
  }

  function pitCanonRewardBoxesForTarget(row,targetLevel){
    const target=pitCanonWhole(targetLevel);
    if(!row?.lootboxMap?.size||target<=0)return {known:false,boxes:0};
    let boxes=0;
    for(let level=0;level<=target;level++)boxes+=pitCanonWhole(row.lootboxMap.get(level));
    return {known:true,boxes};
  }

  function pitCanonRewardTargetLevel(row){
    if(row?.sniper&&!row?.active)return pitCanonWhole(row.sniperTarget);
    const selected=row?.targets?.find(target=>target.id===row.targetId);
    return pitCanonWhole(selected?.level);
  }

  function pitCanonBaseRunMultiplier(row){
    if(row?.active)return Math.max(1,pitCanonWhole(row.activeState?.mass_multiplier??row.activeState?.multiplier)||1);
    if(row?.sniper)return 1;
    const plan=row?.plans?.find(plan=>plan.id===row.planId);
    if(!plan)return 0;
    return row.autofinish?pitCanonWhole(plan.total):pitCanonWhole(plan.chunks?.[0]);
  }

  function pitCanonDefaultDailyBaseRuns(row){
    if(!row||row.sniper)return 0;
    if(row.active)return pitCanonWhole(row.maximum);
    const plan=row?.plans?.find(plan=>plan.id===row.planId);
    return pitCanonWhole(plan?.total);
  }

  function pitCanonDailyBaseRuns(row){
    return row?.dailyBaseRuns===null||row?.dailyBaseRuns===undefined?pitCanonDefaultDailyBaseRuns(row):pitCanonWhole(row.dailyBaseRuns);
  }

  function pitCanonRewardStrategy(value){
    return ['upfront','gradual','last_day'].includes(String(value||''))?String(value):'last_day';
  }

  function pitCanonRewardSchedule(required,strategy,remainingMs){
    const needed=pitCanonWhole(required),normalized=pitCanonRewardStrategy(strategy);
    const divisor=Math.max(1,Math.ceil(Math.max(0,Number(remainingMs)||0)/86400000));
    const activeNow=normalized!=='last_day'||Number(remainingMs)<86400000;
    let requestedNow=0;
    if(normalized==='upfront')requestedNow=needed;
    else if(normalized==='gradual'&&needed>0)requestedNow=Math.ceil(needed/divisor);
    else if(normalized==='last_day'&&activeNow)requestedNow=needed;
    return {strategy:normalized,gradualDivisor:divisor,strategyActiveNow:activeNow,requestedNow};
  }

  function pitCanonRewardPlan(row,minScore){
    const targetLevel=pitCanonRewardTargetLevel(row);
    const points=pitCanonRewardPointsForTarget(row,targetLevel);
    const boxes=pitCanonRewardBoxesForTarget(row,targetLevel);
    const currentScore=pitCanonWhole(row?.currentScore);
    const targetScore=pitCanonWhole(minScore);
    const baseMultiplier=pitCanonBaseRunMultiplier(row);
    const dailyBaseRuns=pitCanonDailyBaseRuns(row);
    const futureRefreshes=pitCanonFutureDailyRefreshCount(row?.tournamentEndTime);
    const todayBasePoints=points.known?points.points*baseMultiplier:0;
    const futureDailyPoints=points.known?points.points*dailyBaseRuns*futureRefreshes:0;
    const scoreAfterDaily=currentScore+todayBasePoints+futureDailyPoints;
    const remainingPoints=Math.max(0,targetScore-scoreAfterDaily);
    const requiredExtraRuns=points.known&&points.points>0?Math.ceil(remainingPoints/points.points):0;
    const remainingMs=Math.max(0,Number(row?.tournamentEndTime||0)-Date.now());
    const schedule=pitCanonRewardSchedule(requiredExtraRuns,row?.rewardStrategy,remainingMs);
    const initialBoxes=boxes.known?boxes.boxes*baseMultiplier:0;
    const futureBoxes=boxes.known?boxes.boxes*dailyBaseRuns*futureRefreshes:0;
    const rewardBoxes=boxes.known?boxes.boxes*requiredExtraRuns:0;
    const existingBoxes=pitCanonWhole(row?.lootboxes);
    const projectedBoxes=existingBoxes+initialBoxes+futureBoxes+rewardBoxes;
    const expectedBoxPasses=Math.floor(projectedBoxes/HK_PIT_LOOTBOX_OPEN_BATCH)*HK_PIT_LOOTBOX_EXPECTED_PASSES;
    const passCost=pitCanonWhole(pitCanonDirectPassCost(row?.state,1,'ITEM')??1)||1;
    const requiredExtraItemCost=requiredExtraRuns*passCost;
    const projectedPasses=pitCanonWhole(row?.itemPasses)+expectedBoxPasses;
    const finalScore=scoreAfterDaily+(requiredExtraRuns*(points.known?points.points:0));
    const tournamentActive=!!row?.tournamentActive;
    const targetExact=targetLevel>0;
    const known=tournamentActive&&targetExact&&points.known;
    const autofinishReady=!!row?.autofinish;
    const reachable=known&&finalScore>=targetScore&&projectedPasses>=requiredExtraItemCost;
    return {
      known,tournamentActive,targetExact,autofinishReady,currentScore,targetScore,targetLevel,
      pointsPerPass:points.points||0,boxesPerPass:boxes.boxes||0,baseMultiplier,dailyBaseRuns,futureRefreshes,
      todayBasePoints,futureDailyPoints,remainingPoints,requiredExtraRuns,requiredExtraItemCost,
      scheduledNow:schedule.requestedNow,strategy:schedule.strategy,gradualDivisor:schedule.gradualDivisor,
      strategyActiveNow:schedule.strategyActiveNow,existingBoxes,projectedBoxes,expectedBoxPasses,
      projectedPasses,finalScore,reachable,valid:reachable&&autofinishReady,alreadyReached:currentScore>=targetScore
    };
  }

  function pitCanonRewardStatus(plan){
    if(!plan?.tournamentActive)return either('Нет активного турнира','No active tournament');
    if(!plan.targetExact)return either('Для расчёта выберите точный целевой уровень','Choose an exact target level for calculation');
    if(!plan.known)return either('Данных для расчёта сейчас недостаточно','Not enough data to calculate');
    if(!plan.autofinishReady)return either('Для планирования награды включите Автозавершение','Enable Auto-finish to plan a reward');
    if(plan.alreadyReached)return either('Цель уже достигнута','Target already reached');
    if(!plan.reachable)return either('По текущему прогнозу ресурсов недостаточно','Current forecast does not have enough resources');
    return either('Цель укладывается в срок турнира','Reward target is on schedule');
  }

  function pitCanonFormatRemaining(endTime){
    let seconds=Math.max(0,Math.floor((Number(endTime||0)-Date.now())/1000));
    const days=Math.floor(seconds/86400);seconds-=days*86400;
    const hours=Math.floor(seconds/3600);seconds-=hours*3600;
    const minutes=Math.floor(seconds/60);
    return days>0?${days}д ${hours}ч:${hours}ч ${minutes}м;
  }

"""
if anchor not in s:
    raise SystemExit('plans anchor missing')
s=s.replace(anchor,helpers+anchor,1)

old_row="""      const row={definition:def,state,activeState,active,available,maximum,itemPasses,paws,plans,targets,sniperTargets,
        enabled:false,planId:selectedPlan?.id||'',targetId:target?.id||'any',
        maxRestoration:Math.min(paws,pitCanonWhole(old.maxRestoration)),autofinish:!!old.autofinish,
        sniper,sniperPayment,sniperTarget,recommendedSniperTarget,sniperCrystalCost,sniperItemCost};
"""
new_row="""      const leaderboard=pitCanonRewardLive.leaderboards?.[def.id]||null;
      const view=pitCanonRewardLive.views?.[def.id]||null;
      const tournamentActive=String(leaderboard?.status||'').toUpperCase()==='ACTUAL';
      const rewardTiers=pitCanonRewardTiers(leaderboard);
      const rewardTargetMin=tournamentActive&&rewardTiers.some(tier=>tier.minScore===pitCanonWhole(old.rewardTargetMin))?pitCanonWhole(old.rewardTargetMin):0;
      const row={definition:def,state,activeState,active,available,maximum,itemPasses,paws,plans,targets,sniperTargets,
        enabled:false,planId:selectedPlan?.id||'',targetId:target?.id||'any',
        maxRestoration:Math.min(paws,pitCanonWhole(old.maxRestoration)),autofinish:!!old.autofinish,
        sniper,sniperPayment,sniperTarget,recommendedSniperTarget,sniperCrystalCost,sniperItemCost,
        scoreMap:pitCanonRewardItemMap(view,def.scoreItemId),lootboxMap:pitCanonRewardItemMap(view,HK_PIT_LOOTBOX_ITEM_ID),
        lootboxes:pitCanonResourceQuantity(documentValue,HK_PIT_LOOTBOX_ITEM_ID,'item'),leaderboard,tournamentActive,
        tournamentEndTime:pitCanonTournamentEndTime(leaderboard),currentScore:tournamentActive?pitCanonWhole(leaderboard?.your_lb_slot?.score):0,
        rewardTiers,rewardTargetMin,dailyBaseRuns:old.dailyBaseRuns==null?null:pitCanonWhole(old.dailyBaseRuns),
        rewardStrategy:pitCanonRewardStrategy(old.rewardStrategy)};
"""
if old_row not in s:
    raise SystemExit('row object anchor missing')
s=s.replace(old_row,new_row,1)

old_save=r"""        sniper,
        sniperPayment:String(box.querySelector(`[data-pit-canon-sniper-payment="${def.id}"]`)?.value||old.sniperPayment||''),
        sniperTarget:sniper&&!active?sniperLevel:pitCanonWhole(old.sniperTarget)
      };
"""
new_save=r"""        sniper,
        sniperPayment:String(box.querySelector(`[data-pit-canon-sniper-payment="${def.id}"]`)?.value||old.sniperPayment||''),
        sniperTarget:sniper&&!active?sniperLevel:pitCanonWhole(old.sniperTarget),
        rewardTargetMin:pitCanonWhole(box.querySelector(`[data-pit-reward-target="${def.id}"]`)?.value??old.rewardTargetMin),
        dailyBaseRuns:box.querySelector(`[data-pit-daily-base-runs="${def.id}"]`)?pitCanonWhole(box.querySelector(`[data-pit-daily-base-runs="${def.id}"]`).value):old.dailyBaseRuns,
        rewardStrategy:pitCanonRewardStrategy(box.querySelector(`[data-pit-reward-strategy="${def.id}"]`)?.value||old.rewardStrategy)
      };
"""
old_save=old_save.replace('`',chr(96)).replaceAll('§'+chr(123),'$'+chr(123))
new_save=new_save.replaceAll('`',chr(96)).replaceAll('§'+chr(123),'$'+chr(123))
if old_save not in s:
    raise SystemExit('save dom anchor missing')
s=s.replace(old_save,new_save,1)

needle=r"""        const paymentOptions=`<option value="FREE" ${row.sniperPayment==='FREE'?'selected':''} ${row.available>0?'':'disabled'}>${either('Бесплатный пропуск','Free pass')}</option><option value="PREM" ${row.sniperPayment==='PREM'?'selected':''} ${row.sniperCrystalCost===null?'disabled':''}>${either('Кристаллы','Crystals')} — 💎 ${pitCanonWhole(row.sniperCrystalCost)}</option><option value="ITEM" ${row.sniperPayment==='ITEM'?'selected':''} ${row.sniperItemCost===null||itemPasses<pitCanonWhole(row.sniperItemCost)?'disabled':''}>${either('Пропуск Ямы','Pit Pass')} — 🎟 ${pitCanonWhole(row.sniperItemCost)}</option>`;
        return `<section class="hk-pit-canon-card ${row.enabled?'selected':''}"><div class="hk-pit-canon-head">"""
replace=r"""        const paymentOptions=`<option value="FREE" ${row.sniperPayment==='FREE'?'selected':''} ${row.available>0?'':'disabled'}>${either('Бесплатный пропуск','Free pass')}</option><option value="PREM" ${row.sniperPayment==='PREM'?'selected':''} ${row.sniperCrystalCost===null?'disabled':''}>${either('Кристаллы','Crystals')} — 💎 ${pitCanonWhole(row.sniperCrystalCost)}</option><option value="ITEM" ${row.sniperPayment==='ITEM'?'selected':''} ${row.sniperItemCost===null||itemPasses<pitCanonWhole(row.sniperItemCost)?'disabled':''}>${either('Пропуск Ямы','Pit Pass')} — 🎟 ${pitCanonWhole(row.sniperItemCost)}</option>`;
        const rewardPlan=row.rewardTargetMin>0?pitCanonRewardPlan(row,row.rewardTargetMin):null;
        const rewardOptions=`<option value="0">${either('Не выбрана','Not selected')}</option>`+row.rewardTiers.map(tier=>`<option value="${tier.minScore}" ${row.rewardTargetMin===tier.minScore?'selected':''}>≥ ${tier.minScore.toLocaleString(locale())}</option>`).join('');
        const strategyOptions=`<option value="upfront" ${row.rewardStrategy==='upfront'?'selected':''}>${either('Сразу','Upfront')}</option><option value="gradual" ${row.rewardStrategy==='gradual'?'selected':''}>${either('Постепенно','Gradual')}</option><option value="last_day" ${row.rewardStrategy==='last_day'?'selected':''}>${either('В последний день','Last day')}</option>`;
        const rewardBlock=row.leaderboard?`<details class="hk-pit-reward-block" ${row.rewardTargetMin>0?'open':''}><summary><span>${either('Турнирная награда','Tournament reward')}</span><b class="${row.tournamentActive?'active':'inactive'}">${row.tournamentActive?either('Активный турнир','Active tournament'):either('Нет активного турнира','No active tournament')}${row.tournamentActive&&row.tournamentEndTime?` · ${pitCanonFormatRemaining(row.tournamentEndTime)}`:''}</b></summary><div class="hk-pit-reward-body"><div class="hk-pit-reward-live"><span>${either('Очки турнира','Tournament points')} <b>${row.currentScore.toLocaleString(locale())}</b></span><span>${either('Коробки дани','Tribute Boxes')} <b>${row.lootboxes.toLocaleString(locale())}</b></span></div><div class="hk-pit-reward-controls"><label><span>${either('Цель по награде','Reward target')}</span><select data-pit-reward-target="${def.id}" ${row.tournamentActive?'':'disabled'}>${rewardOptions}</select></label><label><span>${either('Ежедневные базовые запуски','Daily base runs')}</span><input data-pit-daily-base-runs="${def.id}" type="number" min="0" step="1" value="${pitCanonDailyBaseRuns(row)}"></label><label><span>${either('Стратегия дополнительных Пропусков Ямы','Extra Pit Pass strategy')}</span><select data-pit-reward-strategy="${def.id}">${strategyOptions}</select></label></div>${rewardPlan?`<div class="hk-pit-reward-plan"><div class="hk-pit-reward-stats"><span><small>${either('Очки за x1','Points per x1')}</small><b>${rewardPlan.pointsPerPass.toLocaleString(locale())}</b></span><span><small>${either('Будущих сбросов','Future resets')}</small><b>${rewardPlan.futureRefreshes}</b></span><span><small>${either('Нужно после базы','Needed after base')}</small><b>${rewardPlan.remainingPoints.toLocaleString(locale())}</b></span><span><small>${either('Доп. x1 всего','Extra x1 total')}</small><b>${rewardPlan.requiredExtraRuns}</b></span><span><small>${either('Запланировано сейчас','Scheduled now')}</small><b>${rewardPlan.scheduledNow}</b></span><span><small>${either('Доп. Пропусков','Extra Pit Passes')}</small><b>${rewardPlan.requiredExtraItemCost}</b></span><span><small>${either('Возврат из коробок','Box-return Passes')}</small><b>${rewardPlan.expectedBoxPasses}</b></span><span><small>${either('Прогноз очков','Projected points')}</small><b>${rewardPlan.finalScore.toLocaleString(locale())}</b></span></div><div class="hk-pit-reward-status ${rewardPlan.valid?'good':'warn'}">${escapeHtml(pitCanonRewardStatus(rewardPlan))}</div><small class="hk-pit-reward-note">${either('Сегодня используется выбранный План пропусков. После будущих дневных сбросов — значение «Ежедневные базовые запуски». Каждые полные 100 коробок дани прогнозируются как 2 Пропуска Ямы.','Today uses the selected Pass plan. Future daily resets use Daily base runs. Every full 100 Tribute Boxes is forecast as 2 Pit Passes.')}</small></div>`:''}</div></details>`:'';
        return `<section class="hk-pit-canon-card ${row.enabled?'selected':''}"><div class="hk-pit-canon-head">"""
needle=needle.replaceAll('`',chr(96)).replaceAll('§'+chr(123),'$'+chr(123))
replace=replace.replaceAll('`',chr(96)).replaceAll('§'+chr(123),'$'+chr(123))
if needle not in s:
    raise SystemExit('render payment anchor missing')
s=s.replace(needle,replace,1)

card_end=r"""<label class="hk-pit-canon-check"><span>${either('Автозавершение Ямы','Auto-finish Pit')}</span><input data-pit-canon-autofinish="${def.id}" type="checkbox" ${row.autofinish?'checked':''}></label></div></section>`;"""
card_new=r"""<label class="hk-pit-canon-check"><span>${either('Автозавершение Ямы','Auto-finish Pit')}</span><input data-pit-canon-autofinish="${def.id}" type="checkbox" ${row.autofinish?'checked':''}></label></div>${rewardBlock}</section>`;"""
card_end=card_end.replaceAll('`',chr(96)).replaceAll('§'+chr(123),'$'+chr(123))
card_new=card_new.replaceAll('`',chr(96)).replaceAll('§'+chr(123),'$'+chr(123))
if card_end not in s:
    raise SystemExit('card end anchor missing')
s=s.replace(card_end,card_new,1)

old_events="""    box.querySelectorAll('[data-pit-canon-enabled],[data-pit-canon-plan],[data-pit-canon-target],[data-pit-canon-paws],[data-pit-canon-autofinish],[data-pit-canon-sniper],[data-pit-canon-sniper-payment]').forEach(input=>{input.onchange=()=>{pitCanonSaveDom();pitCanonRender();};});
"""
new_events="""    box.querySelectorAll('[data-pit-canon-enabled],[data-pit-canon-plan],[data-pit-canon-target],[data-pit-canon-paws],[data-pit-canon-autofinish],[data-pit-canon-sniper],[data-pit-canon-sniper-payment],[data-pit-reward-target],[data-pit-daily-base-runs],[data-pit-reward-strategy]').forEach(input=>{input.onchange=()=>{pitCanonSaveDom();pitCanonRender();};});
"""
if old_events not in s:
    raise SystemExit('render event anchor missing')
s=s.replace(old_events,new_events,1)

old_busy="[data-pit-canon-enabled],[data-pit-canon-plan],[data-pit-canon-target],[data-pit-canon-paws],[data-pit-canon-autofinish],[data-pit-canon-sniper],[data-pit-canon-sniper-payment],#hk-pits-autofinish-all,#hk-pits-start"
new_busy="[data-pit-canon-enabled],[data-pit-canon-plan],[data-pit-canon-target],[data-pit-canon-paws],[data-pit-canon-autofinish],[data-pit-canon-sniper],[data-pit-canon-sniper-payment],[data-pit-reward-target],[data-pit-daily-base-runs],[data-pit-reward-strategy],#hk-pits-autofinish-all,#hk-pits-start"
if old_busy not in s:
    raise SystemExit('busy selector anchor missing')
s=s.replace(old_busy,new_busy,1)

old_refresh=r"""        if (key === 'pit') {
          playerDocument = await apiJson('/player/me','POST');
          acceptPitDocument(${apiBase}/player/me`,playerDocument);
          pitCanonRender();
          liveReadOk=true;return playerDocument;
        }
"""
new_refresh=r"""        if (key === 'pit') {
          const results=await Promise.all([apiJson('/player/me','POST'),pitCanonLoadRewardLive()]);
          playerDocument=results[0];
          acceptPitDocument(${apiBase}/player/me`,playerDocument);
          pitCanonRender();
          liveReadOk=true;return playerDocument;
        }
"""
old_refresh=old_refresh.replaceAll('`',chr(96)).replaceAll('§'+chr(123),'$'+chr(123))
new_refresh=new_refresh.replaceAll('`',chr(96)).replaceAll('§'+chr(123),'$'+chr(123))
if old_refresh not in s:
    raise SystemExit('pit refresh anchor missing')
s=s.replace(old_refresh,new_refresh,1)

css_anchor=".hk-pit-decision-actions button:disabled{opacity:.45}"
css_add=".hk-pit-reward-block{margin-top:10px;border:1px solid #33455f;border-radius:11px;background:#0a1019}.hk-pit-reward-block>summary{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:9px 10px;cursor:pointer;font-size:11px;font-weight:800}.hk-pit-reward-block>summary b{font-size:9px;color:#8fa1b8}.hk-pit-reward-block>summary b.active{color:#7fe0ad}.hk-pit-reward-body{display:grid;gap:9px;padding:0 10px 10px}.hk-pit-reward-live{display:flex;flex-wrap:wrap;gap:8px}.hk-pit-reward-live span{padding:6px 8px;border-radius:8px;background:#111a27;color:#93a4ba;font-size:9px}.hk-pit-reward-live b{color:#e7edf5}.hk-pit-reward-controls{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px}.hk-pit-reward-controls label{display:grid;gap:4px}.hk-pit-reward-controls label>span{color:#8fa1b8;font-size:9px}.hk-pit-reward-controls select,.hk-pit-reward-controls input{width:100%;box-sizing:border-box}.hk-pit-reward-plan{display:grid;gap:7px}.hk-pit-reward-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px}.hk-pit-reward-stats span{padding:7px;border-radius:8px;background:#0e1723}.hk-pit-reward-stats small{display:block;color:#7f91a9;font-size:8px}.hk-pit-reward-stats b{display:block;margin-top:2px;font-size:11px}.hk-pit-reward-status{padding:7px 8px;border-radius:8px;font-size:10px;font-weight:800}.hk-pit-reward-status.good{background:#153524;color:#7fe0ad}.hk-pit-reward-status.warn{background:#392c13;color:#ffd166}.hk-pit-reward-note{color:#78889d;font-size:8px;line-height:1.35}@media(max-width:760px){.hk-pit-reward-controls{grid-template-columns:1fr}.hk-pit-reward-stats{grid-template-columns:repeat(2,minmax(0,1fr))}}"
if css_anchor not in s:
    raise SystemExit('reward css anchor missing')
s=s.replace(css_anchor,css_anchor+css_add,1)

bad="return days>0?${days}д ${hours}ч:${hours}ч ${minutes}м;"
bt=chr(96); dlr='$'
good="return days>0?"+bt+dlr+"{days}д "+dlr+"{hours}ч"+bt+":"+bt+dlr+"{hours}ч "+dlr+"{minutes}м"+bt+";"
s=s.replace(bad,good)

for needle in [
    MARK,
    "function pitCanonLoadRewardLive()",
    "function pitCanonRewardPlan(row,minScore)",
    "data-pit-reward-target",
    "data-pit-daily-base-runs",
    "data-pit-reward-strategy",
    "HK_PIT_LOOTBOX_OPEN_BATCH = 100",
    "pitCanonFutureDailyRefreshCount"
]:
    if needle not in s:
        raise SystemExit('missing r12 invariant: '+needle)

p.write_text(s,encoding='utf-8')
print('PITS_REWARD_PLANNER_R12_PATCH_OK')
