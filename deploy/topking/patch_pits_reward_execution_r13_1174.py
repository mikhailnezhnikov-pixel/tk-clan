from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')

BASE="const HK_PITS_REWARD_REV = 'pits-reward-planner-core-20260920-r12';"
MARK="const HK_PITS_REWARD_EXEC_REV = 'pits-reward-execution-20260920-r13';"
if MARK in s: raise SystemExit('already applied')
if BASE not in s: raise SystemExit('r12 marker missing')
s=s.replace(BASE,BASE+"\n  "+MARK,1)

anchor="  function pitCanonPlans(state,available,itemPasses) {\n"
helpers=r"""  function pitCanonRewardItemBatches(row){
    const result=[];
    for(const batch of HK_PITS_CANON_BATCHES){
      const cost=pitCanonDirectPassCost(row?.state,batch,'ITEM');
      if(cost!==null&&pitCanonWhole(cost)>0)result.push({batch,cost:pitCanonWhole(cost)});
    }
    return result;
  }

  function pitCanonRewardDecomposeWithBatches(supported,total){
    let remaining=pitCanonWhole(total),steps=[],cost=0;
    const options=[...(supported||[])].filter(row=>pitCanonWhole(row.batch)>0&&pitCanonWhole(row.cost)>0).sort((a,b)=>b.batch-a.batch);
    for(const option of options){
      const batch=pitCanonWhole(option.batch),unitCost=pitCanonWhole(option.cost);
      while(remaining>=batch){
        steps.push({chunk:batch,payment:'ITEM',source:'reward'});
        cost+=unitCost;
        remaining-=batch;
      }
    }
    return {steps,cost,remaining};
  }

  function pitCanonRewardStrategyRequestedNow(required,strategy,{completed=0,gradualDivisor=1,strategyActiveNow=true}={}){
    const normalized=pitCanonRewardStrategy(strategy),needed=pitCanonWhole(required),done=pitCanonWhole(completed),divisor=Math.max(1,pitCanonWhole(gradualDivisor));
    if(normalized==='upfront')return needed;
    if(normalized==='gradual'&&needed>0)return Math.max(0,Math.ceil((needed+done)/divisor)-done);
    if(normalized==='last_day'&&strategyActiveNow)return needed;
    return 0;
  }

  function pitCanonRewardRunMeta(row){
    const minScore=pitCanonWhole(row?.rewardTargetMin);
    const plan=minScore>0?pitCanonRewardPlan(row,minScore):null;
    const supported=pitCanonRewardItemBatches(row);
    const canExecute=!!(plan?.valid&&plan?.known&&row?.autofinish&&supported.length);
    const requested=canExecute?pitCanonWhole(plan.scheduledNow):0;
    const decomp=pitCanonRewardDecomposeWithBatches(supported,requested);
    const safeSteps=decomp.remaining===0?decomp.steps:[];
    const safeCost=decomp.remaining===0?decomp.cost:0;
    return {
      enabled:canExecute,
      minScore:canExecute?minScore:0,
      plannedFinalScore:canExecute?pitCanonWhole(plan.finalScore):0,
      pointsPerPass:canExecute?pitCanonWhole(plan.pointsPerPass):0,
      boxesPerPass:canExecute?pitCanonWhole(plan.boxesPerPass):0,
      futureDailyPoints:canExecute?pitCanonWhole(plan.futureDailyPoints):0,
      futureExtraPoints:canExecute?Math.max(0,pitCanonWhole(plan.requiredExtraRuns)-requested)*pitCanonWhole(plan.pointsPerPass):0,
      strategy:canExecute?pitCanonRewardStrategy(plan.strategy):'last_day',
      strategyActiveNow:canExecute?!!plan.strategyActiveNow:false,
      gradualDivisor:canExecute?Math.max(1,pitCanonWhole(plan.gradualDivisor)):1,
      itemBatches:supported.map(row=>({...row})),
      steps:safeSteps,
      itemCost:safeCost
    };
  }

  async function pitCanonLiveLeaderboardScore(def){
    try{
      const payload={leaderboard_type:def.leaderboardType};
      if(def.leaderboardStatus)payload.leaderboard_status=def.leaderboardStatus;
      const leaderboard=await apiJson('/leaderboard','POST',payload);
      pitCanonRewardLive.leaderboards[def.id]=leaderboard;
      if(String(leaderboard?.status||'').toUpperCase()!=='ACTUAL')return null;
      return pitCanonWhole(leaderboard?.your_lb_slot?.score);
    }catch(error){
      pitCanonRunnerLog(¤§{pitCanonDefinitionName(def)} — §{either('не удалось обновить очки турнира','could not refresh tournament score')}: §{error?.message||error}¤,'warn');
      return null;
    }
  }

  async function pitCanonOpenRewardLootboxes(){
    let openedTotal=0,gainedTotal=0;
    for(let guard=0;guard<100;guard++){
      const beforeBoxes=pitCanonResourceQuantity(playerDocument,HK_PIT_LOOTBOX_ITEM_ID,'item');
      if(beforeBoxes<HK_PIT_LOOTBOX_OPEN_BATCH)break;
      const beforePasses=pitCanonResourceQuantity(playerDocument,HK_PIT_PASS_ITEM_ID,'item');
      hkRunner.setStep(¤§{either('Открытие коробок дани','Opening Tribute Boxes')} ×§{HK_PIT_LOOTBOX_OPEN_BATCH}¤,hkRunner.state.done,hkRunner.state.total);
      pitCanonRunnerLog(¤§{either('Коробки дани — открытие','Tribute Boxes — opening')}: ×§{HK_PIT_LOOTBOX_OPEN_BATCH}¤,'info');
      await apiJson(¤/player/boxes/open?item_id=§{encodeURIComponent(HK_PIT_LOOTBOX_ITEM_ID)}&quantity=§{HK_PIT_LOOTBOX_OPEN_BATCH}¤,'POST');
      playerDocument=await hkAuthoritativePlayerRead('pits:reward-lootboxes');
      const afterBoxes=pitCanonResourceQuantity(playerDocument,HK_PIT_LOOTBOX_ITEM_ID,'item');
      const afterPasses=pitCanonResourceQuantity(playerDocument,HK_PIT_PASS_ITEM_ID,'item');
      const opened=Math.max(0,beforeBoxes-afterBoxes),gained=Math.max(0,afterPasses-beforePasses);
      openedTotal+=opened;gainedTotal+=gained;
      pitCanonRunnerLog(¤✓ §{either('Коробки дани открыты','Tribute Boxes opened')}: §{opened||HK_PIT_LOOTBOX_OPEN_BATCH} · 🎟 +§{gained} · §{either('осталось коробок','boxes remaining')}: §{afterBoxes}¤,'ok');
      if(afterBoxes>=beforeBoxes)break;
    }
    return {opened:openedTotal,gained:gainedTotal};
  }

  function pitCanonRecalculateRewardContinuation(config,completedIndex,liveScore){
    if(pitCanonWhole(config?.rewardMinScore)<=0||pitCanonWhole(config?.rewardPointsPerPass)<=0||liveScore===null)return null;
    const future=config.steps.slice(completedIndex+1);
    const futureBase=future.filter(step=>step.source!=='reward');
    const futureReward=future.filter(step=>step.source==='reward');
    const oldMultiplier=futureReward.reduce((sum,step)=>sum+pitCanonWhole(step.chunk),0);
    const completedRewardMultiplier=config.steps.slice(0,completedIndex+1).filter(step=>step.source==='reward').reduce((sum,step)=>sum+pitCanonWhole(step.chunk),0);
    const futureBaseMultiplier=futureBase.reduce((sum,step)=>sum+pitCanonWhole(step.chunk),0);
    const futureBasePoints=futureBaseMultiplier*pitCanonWhole(config.rewardPointsPerPass);
    const scoreAfterDaily=pitCanonWhole(liveScore)+futureBasePoints+pitCanonWhole(config.rewardFutureDailyPoints);
    const remainingPoints=Math.max(0,pitCanonWhole(config.rewardMinScore)-scoreAfterDaily);
    const remainingRuns=remainingPoints>0?Math.ceil(remainingPoints/pitCanonWhole(config.rewardPointsPerPass)):0;
    const newMultiplier=pitCanonRewardStrategyRequestedNow(remainingRuns,config.rewardStrategy,{
      completed:completedRewardMultiplier,
      gradualDivisor:config.rewardGradualDivisor,
      strategyActiveNow:config.rewardStrategyActiveNow
    });
    config.rewardFutureExtraPoints=Math.max(0,remainingRuns-newMultiplier)*pitCanonWhole(config.rewardPointsPerPass);
    if(newMultiplier===oldMultiplier)return null;
    const decomp=pitCanonRewardDecomposeWithBatches(config.rewardItemBatches,newMultiplier);
    if(decomp.remaining>0)return null;
    const oldFutureCost=futureReward.reduce((sum,step)=>{
      const option=(config.rewardItemBatches||[]).find(row=>pitCanonWhole(row.batch)===pitCanonWhole(step.chunk));
      return sum+pitCanonWhole(option?.cost);
    },0);
    const oldLength=config.steps.length;
    config.steps=[...config.steps.slice(0,completedIndex+1),...futureBase,...decomp.steps];
    config.itemPassBudget=Math.max(0,pitCanonWhole(config.itemPassBudget)+decomp.cost-oldFutureCost);
    return {before:oldMultiplier,after:newMultiplier,deltaRounds:config.steps.length-oldLength};
  }

"""
helpers=helpers.replace('¤',chr(96)).replace('§'+chr(123),'$'+chr(123))
if anchor not in s: raise SystemExit('reward helper insertion anchor missing')
s=s.replace(anchor,helpers+anchor,1)

start=s.index("  function pitCanonReadRunConfigs() {")
end=s.index("  function pitCanonRunnerLog",start)
new_read=r"""  function pitCanonReadRunConfigs() {
    pitCanonSaveDom();
    const rows=pitCanonBuildRows();
    return rows.filter(row=>row.enabled).map(row=>{
      const standaloneSniper=row.sniper&&!row.active;
      const target=standaloneSniper
        ? {id:¤minimum:§{pitCanonWhole(row.sniperTarget)}¤,level:pitCanonWhole(row.sniperTarget)}
        : (row.targets.find(x=>x.id===row.targetId)||row.targets[0]);
      const reward=pitCanonRewardRunMeta(row);
      let base=null;
      if(row.active){
        const chunk=Math.max(1,pitCanonWhole(row.activeState?.mass_multiplier ?? row.activeState?.multiplier));
        base={definition:row.definition,planId:'active',steps:[{chunk,payment:'ACTIVE',source:'base'}],target:pitCanonWhole(target?.level),maxRestoration:row.maxRestoration,autofinish:row.autofinish,resume:true,crystalBudget:0,itemPassBudget:0,sniper:!!row.sniper,sniperPayment:'ACTIVE'};
      }else if(row.sniper){
        if(!pitCanonRowRunnable(row))return null;
        base={definition:row.definition,planId:'sniper-1',steps:[{chunk:1,payment:row.sniperPayment||'FREE',source:'base'}],target:pitCanonWhole(row.sniperTarget),maxRestoration:row.maxRestoration,autofinish:row.autofinish,resume:false,crystalBudget:row.sniperPayment==='PREM'?pitCanonWhole(row.sniperCrystalCost):0,itemPassBudget:row.sniperPayment==='ITEM'?pitCanonWhole(row.sniperItemCost):0,sniper:true,sniperPayment:row.sniperPayment};
      }else{
        const plan=row.plans.find(x=>x.id===row.planId);if(!plan)return null;
        const chunks=row.autofinish?[...plan.chunks]:plan.chunks.slice(0,1);
        base={definition:row.definition,planId:plan.id,steps:chunks.map(chunk=>({chunk,payment:plan.paymentMode,source:'base'})),target:pitCanonWhole(target?.level),maxRestoration:row.maxRestoration,autofinish:row.autofinish,resume:false,crystalBudget:pitCanonWhole(plan.crystalCost),itemPassBudget:pitCanonWhole(plan.itemCost),sniper:false,sniperPayment:''};
      }
      if(!base)return null;
      if(reward.enabled&&reward.steps.length){
        base.steps.push(...reward.steps.map(step=>({...step})));
        base.itemPassBudget+=pitCanonWhole(reward.itemCost);
      }
      Object.assign(base,{
        rewardMinScore:reward.minScore,
        rewardPlannedFinalScore:reward.plannedFinalScore,
        rewardPointsPerPass:reward.pointsPerPass,
        rewardBoxesPerPass:reward.boxesPerPass,
        rewardFutureDailyPoints:reward.futureDailyPoints,
        rewardFutureExtraPoints:reward.futureExtraPoints,
        rewardStrategy:reward.strategy,
        rewardStrategyActiveNow:reward.strategyActiveNow,
        rewardGradualDivisor:reward.gradualDivisor,
        rewardItemBatches:reward.itemBatches
      });
      return base;
    }).filter(config=>config?.steps?.length);
  }

"""
new_read=new_read.replace('¤',chr(96)).replace('§'+chr(123),'$'+chr(123))
s=s[:start]+new_read+s[end:]

needle=r"""        let payment=step.payment;if(payment==='AUTO')payment=available>=chunk?'FREE':'PREM';
        const premCost=payment==='PREM'?pitCanonDirectPassCost(state,chunk,'PREM'):0,itemCost=payment==='ITEM'?pitCanonDirectPassCost(state,chunk,'ITEM'):0;
"""
replace=r"""        let payment=step.payment;if(payment==='AUTO')payment=available>=chunk?'FREE':'PREM';
        if(step.source==='reward'&&payment==='ITEM'){
          let have=pitCanonResourceQuantity(playerDocument,HK_PIT_PASS_ITEM_ID,'item');
          let rewardCost=pitCanonDirectPassCost(state,chunk,'ITEM');
          if(rewardCost!==null&&have<pitCanonWhole(rewardCost)&&pitCanonResourceQuantity(playerDocument,HK_PIT_LOOTBOX_ITEM_ID,'item')>=HK_PIT_LOOTBOX_OPEN_BATCH){
            await pitCanonOpenRewardLootboxes();
            playerDocument=await hkAuthoritativePlayerRead(¤pits:§{def.id}:reward-pass-reread¤);
            state=pitRaceSnapshot(def.id,playerDocument);
            have=pitCanonResourceQuantity(playerDocument,HK_PIT_PASS_ITEM_ID,'item');
            rewardCost=pitCanonDirectPassCost(state,chunk,'ITEM');
          }
          if(rewardCost===null||have<pitCanonWhole(rewardCost)){
            const removed=config.steps.length-index;
            config.steps.splice(index);
            progress.total=Math.max(progress.done,progress.total-removed);
            hkRunner.setStep(¤§{pitCanonDefinitionName(def)} · §{either('турнирный план остановлен — не хватает Пропусков Ямы','reward plan stopped — not enough Pit Passes')}¤,progress.done,progress.total);
            pitCanonRunnerLog(¤§{pitCanonDefinitionName(def)} — §{either('турнирный план безопасно остановлен: фактических Пропусков Ямы недостаточно','reward plan stopped safely: actual Pit Pass balance is insufficient')}¤,'warn');
            break;
          }
        }
        if(index>=config.steps.length)break;
        step=config.steps[index];chunk=pitCanonWhole(step.chunk);payment=step.payment;if(payment==='AUTO')payment=available>=chunk?'FREE':'PREM';
        const premCost=payment==='PREM'?pitCanonDirectPassCost(state,chunk,'PREM'):0,itemCost=payment==='ITEM'?pitCanonDirectPassCost(state,chunk,'ITEM'):0;
"""
replace=replace.replace('¤',chr(96)).replace('§'+chr(123),'$'+chr(123))
if needle not in s: raise SystemExit('reward-step safety anchor missing')
s=s.replace(needle,replace,1)

needle=r"""      progress.done+=1;hkRunner.setStep(¤§{pitCanonDefinitionName(def)} · §{either('раунд завершён','round completed')}¤,progress.done,progress.total);pitCanonRunnerLog(¤✓ §{pitCanonDefinitionName(def)}: ×§{chunk} · 🐾 §{restorationSpent}§{config.autofinish?¤ · §{either('автозавершение','auto-finish')}¤:''}¤,'ok');
      if(!config.autofinish)break;
"""
replace=r"""      progress.done+=1;hkRunner.setStep(¤§{pitCanonDefinitionName(def)} · §{either('раунд завершён','round completed')}¤,progress.done,progress.total);pitCanonRunnerLog(¤✓ §{pitCanonDefinitionName(def)}: ×§{chunk} · 🐾 §{restorationSpent}§{config.autofinish?¤ · §{either('автозавершение','auto-finish')}¤:''}¤,'ok');
      if(config.rewardMinScore>0){
        const liveScore=await pitCanonLiveLeaderboardScore(def);
        if(liveScore!==null){
          if(liveScore>=config.rewardMinScore){
            pitCanonRunnerLog(¤✓ §{pitCanonDefinitionName(def)} — §{either('цель турнирной награды достигнута','tournament reward target reached')}: §{liveScore.toLocaleString(locale())} / §{config.rewardMinScore.toLocaleString(locale())}¤,'ok');
          }
          const result=pitCanonRecalculateRewardContinuation(config,index,liveScore);
          if(result){
            progress.total=Math.max(progress.done,progress.total+result.deltaRounds);
            hkRunner.setStep(¤§{pitCanonDefinitionName(def)} · §{either('турнирный план пересчитан','reward plan recalculated')} §{result.before} → §{result.after}¤,progress.done,progress.total);
            pitCanonRunnerLog(¤§{pitCanonDefinitionName(def)} — §{either('дополнительные x1 пересчитаны','extra x1 recalculated')}: §{result.before} → §{result.after}¤,'info');
          }
          const projected=liveScore+pitCanonWhole(config.rewardFutureDailyPoints)+pitCanonWhole(config.rewardFutureExtraPoints);
          if(liveScore<config.rewardMinScore&&projected>=config.rewardMinScore){
            pitCanonRunnerLog(¤✓ §{pitCanonDefinitionName(def)} — §{either('цель остаётся по графику с будущими запусками','target remains on schedule with future runs')}¤,'ok');
          }
        }
      }
      if(!config.autofinish)break;
"""
needle=needle.replace('¤',chr(96)).replace('§'+chr(123),'$'+chr(123))
replace=replace.replace('¤',chr(96)).replace('§'+chr(123),'$'+chr(123))
if needle not in s: raise SystemExit('round completion reward recalc anchor missing')
s=s.replace(needle,replace,1)

needle="""      playerDocument=await hkAuthoritativePlayerRead('pits:prepare');
      for(const config of configs)await pitCanonRunOne(config,progress);
"""
replace="""      playerDocument=await hkAuthoritativePlayerRead('pits:prepare');
      if(configs.some(config=>pitCanonWhole(config.rewardMinScore)>0)&&pitCanonResourceQuantity(playerDocument,HK_PIT_LOOTBOX_ITEM_ID,'item')>=HK_PIT_LOOTBOX_OPEN_BATCH){
        await pitCanonOpenRewardLootboxes();
      }
      for(const config of configs)await pitCanonRunOne(config,progress);
"""
if needle not in s: raise SystemExit('run prepare reward boxes anchor missing')
s=s.replace(needle,replace,1)

needle="""recordDiagnostic('pits-run-config-snapshot',{pits:configs.map(config=>({id:config.definition?.id,planId:config.planId,steps:config.steps?.length||0,sniper:!!config.sniper,target:config.target}))});"""
replace="""recordDiagnostic('pits-run-config-snapshot',{pits:configs.map(config=>({id:config.definition?.id,planId:config.planId,steps:config.steps?.length||0,sniper:!!config.sniper,target:config.target,rewardMinScore:config.rewardMinScore||0,rewardSteps:config.steps?.filter(step=>step.source==='reward').reduce((sum,step)=>sum+pitCanonWhole(step.chunk),0)||0}))});"""
if needle not in s: raise SystemExit('diagnostic anchor missing')
s=s.replace(needle,replace,1)

for needle in [
    MARK,
    "function pitCanonRewardRunMeta(row)",
    "function pitCanonLiveLeaderboardScore(def)",
    "function pitCanonOpenRewardLootboxes()",
    "function pitCanonRecalculateRewardContinuation(config,completedIndex,liveScore)",
    "source:'reward'",
    "rewardMinScore",
    "дополнительные x1 пересчитаны",
    "player/boxes/open?item_id="
]:
    if needle not in s: raise SystemExit('missing r13 invariant: '+needle)

p.write_text(s,encoding='utf-8')
print('PITS_REWARD_EXECUTION_R13_PATCH_OK')
