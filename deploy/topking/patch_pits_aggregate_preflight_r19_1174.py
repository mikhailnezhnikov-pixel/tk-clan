from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')

BASE="const HK_PITS_REWARD_FIT_REV = 'pits-reward-fit-available-20260920-r18';"
MARK="const HK_PITS_PREFLIGHT_REV = 'pits-aggregate-preflight-20260920-r19';"
if MARK in s: raise SystemExit('already applied')
if BASE not in s: raise SystemExit('r18 marker missing')
s=s.replace(BASE,BASE+"\n  "+MARK,1)

anchor="  function pitCanonModeLabel(config){\n"
helpers="""  function pitCanonPreflightExpectedBoxReturns(pool,useBoxes){
    if(!useBoxes)return;
    const batches=Math.floor(Math.max(0,pitCanonWhole(pool.boxes))/HK_PIT_LOOTBOX_OPEN_BATCH);
    if(batches<=0)return;
    pool.boxes-=batches*HK_PIT_LOOTBOX_OPEN_BATCH;
    pool.passes+=batches*HK_PIT_LOOTBOX_EXPECTED_PASSES;
    pool.openedBoxes+=batches*HK_PIT_LOOTBOX_OPEN_BATCH;
    pool.generatedPasses+=batches*HK_PIT_LOOTBOX_EXPECTED_PASSES;
  }

  function pitCanonPreflightPlan(configs,documentValue=playerDocument){
    const rows=Array.isArray(configs)?configs:[];
    const crystalsAvailable=pitCanonResourceQuantity(documentValue,'cur_prem','currency');
    const pawsAvailable=pitCanonResourceQuantity(documentValue,HK_PIT_RESTORATION_ITEM_ID,'item');
    const crystalsNeeded=rows.reduce((sum,config)=>sum+pitCanonWhole(config.crystalBudget),0);
    const pawsNeeded=rows.reduce((sum,config)=>sum+(pitCanonWhole(config.maxRestoration)*(config.steps?.length||0)),0);
    if(crystalsNeeded>crystalsAvailable)return {ok:false,reason:'crystals',crystalsAvailable,crystalsNeeded,pawsAvailable,pawsNeeded};
    if(pawsNeeded>pawsAvailable)return {ok:false,reason:'paws',crystalsAvailable,crystalsNeeded,pawsAvailable,pawsNeeded};

    const pool={
      passes:pitCanonResourceQuantity(documentValue,HK_PIT_PASS_ITEM_ID,'item'),
      boxes:pitCanonResourceQuantity(documentValue,HK_PIT_LOOTBOX_ITEM_ID,'item'),
      openedBoxes:0,generatedPasses:0
    };
    const useBoxes=rows.some(config=>pitCanonWhole(config.rewardMinScore)>0);

    for(const config of rows){
      pool.passes-=pitCanonWhole(config.baseItemPassBudget);
      const baseMultiplier=(config.steps||[]).filter(step=>step.source!=='reward').reduce((sum,step)=>sum+pitCanonWhole(step.chunk),0);
      pool.boxes+=pitCanonWhole(config.boxesPerPass)*baseMultiplier;
    }
    pitCanonPreflightExpectedBoxReturns(pool,useBoxes);
    if(pool.passes<0)return {ok:false,reason:'passes',crystalsAvailable,crystalsNeeded,pawsAvailable,pawsNeeded,...pool};

    for(const config of rows){
      const queue=(config.steps||[]).filter(step=>step.source==='reward').map(step=>({...step}));
      while(queue.length){
        pitCanonPreflightExpectedBoxReturns(pool,useBoxes);
        const step=queue.shift(),original=pitCanonWhole(step.chunk);
        const supported=[...(config.rewardItemBatches||[])]
          .filter(row=>pitCanonWhole(row.batch)>0&&pitCanonWhole(row.cost)>0)
          .sort((a,b)=>pitCanonWhole(b.batch)-pitCanonWhole(a.batch));
        let option=supported.find(row=>pitCanonWhole(row.batch)===original&&pitCanonWhole(row.cost)<=pitCanonWhole(pool.passes));
        if(!option)option=supported.find(row=>pitCanonWhole(row.batch)<=original&&pitCanonWhole(row.cost)<=pitCanonWhole(pool.passes));
        if(!option)return {ok:false,reason:'passes',crystalsAvailable,crystalsNeeded,pawsAvailable,pawsNeeded,...pool};
        const batch=pitCanonWhole(option.batch);
        pool.passes-=pitCanonWhole(option.cost);
        pool.boxes+=pitCanonWhole(config.boxesPerPass)*batch;
        const remainder=Math.max(0,original-batch);
        if(remainder>0){
          const decomp=pitCanonRewardDecomposeWithBatches(supported,remainder);
          if(decomp.remaining>0)return {ok:false,reason:'passes',crystalsAvailable,crystalsNeeded,pawsAvailable,pawsNeeded,...pool};
          queue.unshift(...decomp.steps.map(next=>({...step,chunk:pitCanonWhole(next.chunk)})));
        }
        pitCanonPreflightExpectedBoxReturns(pool,useBoxes);
      }
    }
    return {ok:true,reason:'',crystalsAvailable,crystalsNeeded,pawsAvailable,pawsNeeded,...pool};
  }

"""
if anchor not in s: raise SystemExit('preflight insertion anchor missing')
s=s.replace(anchor,helpers+anchor,1)

# Attach immutable preflight inputs to configs.
needle="""      if(!base)return null;
      base.startLevel=pitCanonWhole(row.activeState?.level ?? row.state?.level);
      if(reward.enabled&&reward.steps.length){
"""
replace="""      if(!base)return null;
      base.startLevel=pitCanonWhole(row.activeState?.level ?? row.state?.level);
      base.baseItemPassBudget=pitCanonWhole(base.itemPassBudget);
      const boxInfo=pitCanonRewardBoxesForTarget(row,pitCanonWhole(target?.level));
      base.boxesPerPass=boxInfo.known?pitCanonWhole(boxInfo.boxes):0;
      if(reward.enabled&&reward.steps.length){
"""
if needle not in s: raise SystemExit('config preflight metadata anchor missing')
s=s.replace(needle,replace,1)

# Run preflight immediately after authoritative prepare and before opening boxes/actions.
needle="""      playerDocument=await hkAuthoritativePlayerRead('pits:prepare');
      if(configs.some(config=>pitCanonWhole(config.rewardMinScore)>0)&&pitCanonResourceQuantity(playerDocument,HK_PIT_LOOTBOX_ITEM_ID,'item')>=HK_PIT_LOOTBOX_OPEN_BATCH){
"""
replace="""      playerDocument=await hkAuthoritativePlayerRead('pits:prepare');
      const preflight=pitCanonPreflightPlan(configs,playerDocument);
      if(!preflight.ok){
        if(preflight.reason==='crystals')throw new Error(either(
          'Недостаточно кристаллов для всего выбранного плана: нужно '+preflight.crystalsNeeded+', доступно '+preflight.crystalsAvailable,
          'Not enough crystals for the full selected plan: need '+preflight.crystalsNeeded+', available '+preflight.crystalsAvailable
        ));
        if(preflight.reason==='paws')throw new Error(either(
          'Суммарный лимит Лап восстановления превышает запас: нужно до '+preflight.pawsNeeded+', доступно '+preflight.pawsAvailable,
          'Total Restoration Paws limit exceeds balance: need up to '+preflight.pawsNeeded+', available '+preflight.pawsAvailable
        ));
        throw new Error(either(
          'Общий план Пропусков Ямы не помещается в фактический запас даже с доступными возвратами из Коробок дани.',
          'The combined Pit Pass plan does not fit the actual balance even with available Tribute Box returns.'
        ));
      }
      pitCanonRunnerLog('✓ '+either('Предстартовая проверка общего бюджета пройдена','Aggregate preflight budget check passed')+' · 💎 '+preflight.crystalsNeeded+'/'+preflight.crystalsAvailable+' · 🐾 '+preflight.pawsNeeded+'/'+preflight.pawsAvailable+' · 🎟 '+Math.max(0,pitCanonWhole(preflight.passes)),'ok');
      recordDiagnostic('pits-preflight',{ok:true,crystalsNeeded:preflight.crystalsNeeded,crystalsAvailable:preflight.crystalsAvailable,pawsNeeded:preflight.pawsNeeded,pawsAvailable:preflight.pawsAvailable,passesAfterPlan:preflight.passes,boxesAfterPlan:preflight.boxes,openedBoxes:preflight.openedBoxes,generatedPasses:preflight.generatedPasses});
      if(configs.some(config=>pitCanonWhole(config.rewardMinScore)>0)&&pitCanonResourceQuantity(playerDocument,HK_PIT_LOOTBOX_ITEM_ID,'item')>=HK_PIT_LOOTBOX_OPEN_BATCH){
"""
if needle not in s: raise SystemExit('preflight execution anchor missing')
s=s.replace(needle,replace,1)

for needle in [
    MARK,
    "function pitCanonPreflightPlan(configs,documentValue=playerDocument)",
    "base.baseItemPassBudget",
    "base.boxesPerPass",
    "Aggregate preflight budget check passed",
    "pits-preflight"
]:
    if needle not in s: raise SystemExit('missing r19 invariant: '+needle)

p.write_text(s,encoding='utf-8')
print('PITS_AGGREGATE_PREFLIGHT_R19_PATCH_OK')
