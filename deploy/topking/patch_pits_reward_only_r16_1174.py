from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')
BASE="const HK_PITS_SHARED_FORECAST_REV = 'pits-shared-reward-forecast-20260920-r15';"
MARK="const HK_PITS_REWARD_ONLY_REV = 'pits-reward-only-plan-20260920-r16';"
if MARK in s: raise SystemExit('already applied')
if BASE not in s: raise SystemExit('r15 marker missing')
s=s.replace(BASE,BASE+"\n  "+MARK,1)

anchor="  function pitCanonRowRunnable(row) {\n"
helper="""  function pitCanonRewardOnlyPlan(){
    return {id:'reward-0',kind:'reward-zero',total:0,chunks:[],paymentMode:'NONE',crystalCost:0,itemCost:0,affordable:true};
  }

"""
if anchor not in s: raise SystemExit('runnable anchor missing')
s=s.replace(anchor,helper+anchor,1)

needle="""    const plan=row.plans?.find(x=>x.id===row.planId);
    if(!plan)return false;
"""
replace="""    if(row.planId==='reward-0'&&pitCanonWhole(row.rewardTargetMin)>0){
      const reward=pitCanonRewardPlan(row,row.rewardTargetMin);
      return !!reward?.valid;
    }
    const plan=row.plans?.find(x=>x.id===row.planId);
    if(!plan)return false;
"""
if needle not in s: raise SystemExit('runnable plan anchor missing')
s=s.replace(needle,replace,1)

needle="      const selectedPlan=plans.find(row=>row.id===String(old.planId||''))||plans.find(row=>row.kind==='exact')||plans.find(row=>row.affordable)||plans[0]||null;\n"
replace="      let selectedPlan=plans.find(row=>row.id===String(old.planId||''))||plans.find(row=>row.kind==='exact')||plans.find(row=>row.affordable)||plans[0]||null;\n"
if needle not in s: raise SystemExit('selected plan declaration missing')
s=s.replace(needle,replace,1)

needle="""      const rewardTargetMin=tournamentActive&&rewardTiers.some(tier=>tier.minScore===pitCanonWhole(old.rewardTargetMin))?pitCanonWhole(old.rewardTargetMin):0;
      const row={definition:def,state,activeState,active,available,maximum,itemPasses,paws,plans,targets,sniperTargets,
"""
replace="""      const rewardTargetMin=tournamentActive&&rewardTiers.some(tier=>tier.minScore===pitCanonWhole(old.rewardTargetMin))?pitCanonWhole(old.rewardTargetMin):0;
      if(!active&&!sniper&&String(old.planId||'')==='reward-0'&&rewardTargetMin>0)selectedPlan=pitCanonRewardOnlyPlan();
      const row={definition:def,state,activeState,active,available,maximum,itemPasses,paws,plans,targets,sniperTargets,
"""
if needle not in s: raise SystemExit('reward selected-plan anchor missing')
s=s.replace(needle,replace,1)

needle="""  function pitCanonPlanLabel(plan) {
    if(!plan)return either('Нет доступного плана','No available plan');
    const batch=pitCanonDecompose(plan.total).map(value=>`×${value}`).join(' + ');
"""
replace="""  function pitCanonPlanLabel(plan) {
    if(!plan)return either('Нет доступного плана','No available plan');
    if(plan.kind==='reward-zero')return either('Только цель награды — 0 базовых запусков','Reward target only — 0 base runs');
    const batch=pitCanonDecompose(plan.total).map(value=>`×${value}`).join(' + ');
"""
if needle not in s: raise SystemExit('plan label anchor missing')
s=s.replace(needle,replace,1)

needle="""          : row.active
            ? `<option value="active">${either('Продолжить активную Яму','Continue active Pit')} ×${activeBatch||1}</option>`
            : row.plans.map(plan=>`<option value="${escapeHtml(plan.id)}" ${plan.id===row.planId?'selected':''} ${plan.paymentMode==='ITEM'&&!plan.affordable?'disabled':''}>${escapeHtml(pitCanonPlanLabel(plan))}</option>`).join('');
"""
replace="""          : row.active
            ? `<option value="active">${either('Продолжить активную Яму','Continue active Pit')} ×${activeBatch||1}</option>`
            : `${row.rewardTargetMin>0?`<option value="reward-0" ${row.planId==='reward-0'?'selected':''}>${escapeHtml(pitCanonPlanLabel(pitCanonRewardOnlyPlan()))}</option>`:''}${row.plans.map(plan=>`<option value="${escapeHtml(plan.id)}" ${plan.id===row.planId?'selected':''} ${plan.paymentMode==='ITEM'&&!plan.affordable?'disabled':''}>${escapeHtml(pitCanonPlanLabel(plan))}</option>`).join('')}`;
"""
if needle not in s: raise SystemExit('plan options anchor missing')
s=s.replace(needle,replace,1)

needle="""      }else{
        const plan=row.plans.find(x=>x.id===row.planId);if(!plan)return null;
        const chunks=row.autofinish?[...plan.chunks]:plan.chunks.slice(0,1);
        base={definition:row.definition,planId:plan.id,steps:chunks.map(chunk=>({chunk,payment:plan.paymentMode,source:'base'})),target:pitCanonWhole(target?.level),maxRestoration:row.maxRestoration,autofinish:row.autofinish,resume:false,crystalBudget:pitCanonWhole(plan.crystalCost),itemPassBudget:pitCanonWhole(plan.itemCost),sniper:false,sniperPayment:''};
      }
"""
replace="""      }else{
        const plan=row.planId==='reward-0'&&pitCanonWhole(row.rewardTargetMin)>0?pitCanonRewardOnlyPlan():row.plans.find(x=>x.id===row.planId);
        if(!plan)return null;
        const chunks=plan.kind==='reward-zero'?[]:(row.autofinish?[...plan.chunks]:plan.chunks.slice(0,1));
        base={definition:row.definition,planId:plan.id,steps:chunks.map(chunk=>({chunk,payment:plan.paymentMode,source:'base'})),target:pitCanonWhole(target?.level),maxRestoration:row.maxRestoration,autofinish:row.autofinish,resume:false,crystalBudget:pitCanonWhole(plan.crystalCost),itemPassBudget:pitCanonWhole(plan.itemCost),sniper:false,sniperPayment:''};
      }
"""
if needle not in s: raise SystemExit('read config plan anchor missing')
s=s.replace(needle,replace,1)

for x in [
    MARK,
    "function pitCanonRewardOnlyPlan()",
    "kind:'reward-zero'",
    "Только цель награды — 0 базовых запусков",
    "row.planId==='reward-0'",
    "plan.kind==='reward-zero'?[]"
]:
    if x not in s: raise SystemExit('missing r16 invariant: '+x)
p.write_text(s,encoding='utf-8')
print('PITS_REWARD_ONLY_R16_PATCH_OK')
