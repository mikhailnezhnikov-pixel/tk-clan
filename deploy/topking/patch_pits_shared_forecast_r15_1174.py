from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')
BASE="const HK_PITS_SUMMARY_REV = 'pits-plan-totals-20260920-r14';"
MARK="const HK_PITS_SHARED_FORECAST_REV = 'pits-shared-reward-forecast-20260920-r15';"
if MARK in s: raise SystemExit('already applied')
if BASE not in s: raise SystemExit('r14 marker missing')
s=s.replace(BASE,BASE+"\n  "+MARK,1)

anchor="  function pitCanonRewardStatus(plan){\n"
helpers=r"""  function pitCanonPassivePitPassRate(data=playerDocument){
    const rows=Array.isArray(data?.bonuses?.passive_income_item)?data.bonuses.passive_income_item:[];
    const row=rows.find(item=>String(item?.id||'')===HK_PIT_PASS_ITEM_ID)||null;
    if(!row)return 0;
    const num=value=>{const n=Number(value);return Number.isFinite(n)?Math.max(0,n):0};
    return num(row.bonus)+num(row.bonus_building)+(data?.player?.vip_status_applied===true?num(row.vip):0);
  }

  function pitCanonBaseFreePassesUsed(row){
    if(!row||row.sniper)return 0;
    const plan=row.plans?.find(x=>x.id===row.planId);
    if(!plan||plan.paymentMode!=='AUTO')return 0;
    const total=row.active?Math.max(1,pitCanonWhole(row.activeState?.mass_multiplier ?? row.activeState?.multiplier)):(row.autofinish?pitCanonWhole(plan.total):pitCanonWhole(plan.chunks?.[0]));
    return Math.min(pitCanonWhole(row.available),total);
  }

  function pitCanonTournamentFutureFreePasses(row){
    if(!row?.tournamentActive||pitCanonWhole(row?.tournamentEndTime)<=Date.now())return 0;
    const currentUnused=Math.max(0,pitCanonWhole(row.available)-pitCanonBaseFreePassesUsed(row));
    return currentUnused+(pitCanonFutureDailyRefreshCount(row.tournamentEndTime)*pitCanonWhole(row.maximum));
  }

  function pitCanonPlanBoxes(row,future=false){
    const target=pitCanonRewardTargetLevel(row);
    const boxes=pitCanonRewardBoxesForTarget(row,target);
    if(!boxes.known||target<=0)return 0;
    const multiplier=future?pitCanonDailyBaseRuns(row):pitCanonBaseRunMultiplier(row);
    return pitCanonWhole(boxes.boxes)*pitCanonWhole(multiplier);
  }

  function pitCanonPlanItemCost(row){
    if(!row||row.active||row.sniper)return 0;
    const plan=row.plans?.find(x=>x.id===row.planId);
    return plan?.paymentMode==='ITEM'?pitCanonWhole(plan.itemCost):0;
  }

  function pitCanonSharedRewardPool(rows,deadline){
    const source=(rows||[]).filter(row=>row&&row.enabled&&!row.sniper&&pitCanonRowRunnable(row));
    const existingPasses=pitCanonResourceQuantity(playerDocument,HK_PIT_PASS_ITEM_ID,'item');
    const existingBoxes=pitCanonResourceQuantity(playerDocument,HK_PIT_LOOTBOX_ITEM_ID,'item');
    const todayBoxes=source.reduce((sum,row)=>sum+pitCanonPlanBoxes(row,false),0);
    const todayItemCost=source.reduce((sum,row)=>sum+pitCanonPlanItemCost(row),0);
    let futureBoxes=0,futureItemCost=0;
    const limit=pitCanonWhole(deadline);
    if(limit>Date.now()){
      for(const row of source){
        const ownEnd=row.tournamentActive?pitCanonWhole(row.tournamentEndTime):0;
        const horizon=ownEnd>Date.now()?Math.min(limit,ownEnd):limit;
        const refreshes=pitCanonFutureDailyRefreshCount(horizon);
        if(refreshes<=0)continue;
        futureBoxes+=pitCanonPlanBoxes(row,true)*refreshes;
        if(row.dailyBaseRuns===null||row.dailyBaseRuns===undefined)futureItemCost+=pitCanonPlanItemCost(row)*refreshes;
      }
    }
    const passive=Math.floor((pitCanonPassivePitPassRate(playerDocument)*(Math.max(0,limit-Date.now())/3600000))+1e-9);
    const totalBoxes=existingBoxes+todayBoxes+futureBoxes;
    const generatedPasses=Math.floor(totalBoxes/HK_PIT_LOOTBOX_OPEN_BATCH)*HK_PIT_LOOTBOX_EXPECTED_PASSES;
    const passesAfterDaily=existingPasses-todayItemCost-futureItemCost+passive+generatedPasses;
    return {existingPasses,existingBoxes,todayBoxes,todayItemCost,futureBoxes,futureItemCost,passive,totalBoxes,generatedPasses,passesAfterDaily};
  }

  function pitCanonMaxReachableReward(row,pool){
    let best=null;
    for(const tier of [...(row?.rewardTiers||[])].sort((a,b)=>a.minScore-b.minScore)){
      const plan=pitCanonRewardPlan(row,tier.minScore);
      if(plan.known&&plan.finalScore>=tier.minScore&&pitCanonWhole(pool?.passesAfterDaily)>=pitCanonWhole(plan.requiredExtraItemCost))best=tier;
    }
    return best;
  }

  function pitCanonRewardSharedForecastHtml(row,rows){
    if(!row?.tournamentActive||!row?.tournamentEndTime)return '';
    const pool=pitCanonSharedRewardPool(rows,row.tournamentEndTime);
    const maxTier=pitCanonMaxReachableReward(row,pool);
    const maxText=maxTier?'≥ '+pitCanonWhole(maxTier.minScore).toLocaleString(locale()):either('Нет','None');
    const freePasses=pitCanonTournamentFutureFreePasses(row);
    return '<div class="hk-pit-shared-forecast"><b>'+either('Прогноз турнира','Tournament forecast')+'</b><div class="hk-pit-shared-grid">'
      +'<span><small>'+either('Имеющиеся Пропуски Ямы','Existing Pit Passes')+'</small><strong>🎟 '+pool.existingPasses.toLocaleString(locale())+'</strong></span>'
      +'<span><small>'+either('Планы Ям до конца турнира','Pit plans until tournament end')+'</small><strong>− 🎟 '+(pool.todayItemCost+pool.futureItemCost).toLocaleString(locale())+'</strong></span>'
      +'<span><small>'+either('Коробки дани до конца турнира','Tribute Boxes before tournament end')+'</small><strong>□ '+pool.totalBoxes.toLocaleString(locale())+' → 🎟 +'+pool.generatedPasses.toLocaleString(locale())+'</strong></span>'
      +'<span><small>'+either('Пассивные Пропуска до конца','Passive Pit Passes until end')+'</small><strong>🎟 +'+pool.passive.toLocaleString(locale())+'</strong></span>'
      +'<span><small>'+either('Прогноз общего запаса','Projected shared Pit Passes')+'</small><strong>🎟 '+Math.max(0,pool.passesAfterDaily).toLocaleString(locale())+'</strong></span>'
      +'<span><small>'+either('Бесплатные запуски до конца','Free Pit runs until end')+'</small><strong>~'+freePasses.toLocaleString(locale())+'</strong></span>'
      +'<span><small>'+either('Максимально достижимая цель награды','Maximum reachable reward target')+'</small><strong>'+maxText+'</strong></span>'
      +'</div></div>';
  }

"""
if anchor not in s: raise SystemExit('reward status anchor missing')
s=s.replace(anchor,helpers+anchor,1)

needle="        const rewardPlan=row.rewardTargetMin>0?pitCanonRewardPlan(row,row.rewardTargetMin):null;\n"
replace=needle+"        const sharedForecast=pitCanonRewardSharedForecastHtml(row,rows);\n"
if needle not in s: raise SystemExit('reward plan render anchor missing')
s=s.replace(needle,replace,1)

needle='<div class="hk-pit-reward-body"><div class="hk-pit-reward-live">'
replace='<div class="hk-pit-reward-body">§{sharedForecast}<div class="hk-pit-reward-live">'
if needle not in s: raise SystemExit('reward body anchor missing')
s=s.replace(needle,replace,1)
s=s.replace('§'+chr(123),'$'+chr(123))

css_anchor=".hk-pit-reward-note{color:#78889d;font-size:8px;line-height:1.35}"
css_add=".hk-pit-shared-forecast{display:grid;gap:7px;padding:9px;border:1px solid #40516b;border-radius:10px;background:#0d1520}.hk-pit-shared-forecast>b{font-size:10px;color:#d9e5f5}.hk-pit-shared-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.hk-pit-shared-grid span{display:block;padding:6px;border-radius:8px;background:#121c2a}.hk-pit-shared-grid small{display:block;color:#8293aa;font-size:8px}.hk-pit-shared-grid strong{display:block;margin-top:2px;font-size:10px}@media(max-width:560px){.hk-pit-shared-grid{grid-template-columns:1fr}}"
if css_anchor not in s: raise SystemExit('reward note css anchor missing')
s=s.replace(css_anchor,css_anchor+css_add,1)

for x in [MARK,"function pitCanonPassivePitPassRate","function pitCanonSharedRewardPool","function pitCanonMaxReachableReward","function pitCanonRewardSharedForecastHtml","Прогноз общего запаса"]:
    if x not in s: raise SystemExit('missing r15 invariant: '+x)
p.write_text(s,encoding='utf-8')
print('PITS_SHARED_REWARD_FORECAST_R15_PATCH_OK')
