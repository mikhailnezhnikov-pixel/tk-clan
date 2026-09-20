from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')

BASE="const HK_PITS_PREVIEW_REV = 'pits-runtime-preview-20260920-r17';"
MARK="const HK_PITS_REWARD_FIT_REV = 'pits-reward-fit-available-20260920-r18';"
if MARK in s: raise SystemExit('already applied')
if BASE not in s: raise SystemExit('r17 marker missing')
s=s.replace(BASE,BASE+"\n  "+MARK,1)

anchor="  function pitCanonRewardStrategyRequestedNow(required,strategy,{completed=0,gradualDivisor=1,strategyActiveNow=true}={}){\n"
helper="""  function pitCanonFitRewardStepToAvailable(config,index,availablePasses){
    const current=config?.steps?.[index];
    if(current?.source!=='reward')return {changed:false,deltaRounds:0,before:0,after:0};
    const original=pitCanonWhole(current.chunk);
    const options=[...(config.rewardItemBatches||[])]
      .filter(row=>pitCanonWhole(row.batch)>0&&pitCanonWhole(row.cost)>0)
      .sort((a,b)=>pitCanonWhole(b.batch)-pitCanonWhole(a.batch))
      .filter(row=>pitCanonWhole(row.batch)<=original&&pitCanonWhole(row.cost)<=pitCanonWhole(availablePasses));
    const chosen=options[0];
    if(!chosen||pitCanonWhole(chosen.batch)===original)return {changed:false,deltaRounds:0,before:original,after:original};
    const remainder=Math.max(0,original-pitCanonWhole(chosen.batch));
    const decomp=pitCanonRewardDecomposeWithBatches(config.rewardItemBatches,remainder);
    if(decomp.remaining>0)return {changed:false,deltaRounds:0,before:original,after:original};
    const replacement=[{...current,chunk:pitCanonWhole(chosen.batch)},...decomp.steps.map(step=>({...current,chunk:pitCanonWhole(step.chunk)}) )];
    const originalOption=(config.rewardItemBatches||[]).find(row=>pitCanonWhole(row.batch)===original);
    const oldCost=pitCanonWhole(originalOption?.cost);
    const newCost=pitCanonWhole(chosen.cost)+pitCanonWhole(decomp.cost);
    config.steps.splice(index,1,...replacement);
    config.itemPassBudget=Math.max(0,pitCanonWhole(config.itemPassBudget)+newCost-oldCost);
    return {changed:true,deltaRounds:replacement.length-1,before:original,after:pitCanonWhole(chosen.batch),replacement:replacement.map(step=>pitCanonWhole(step.chunk))};
  }

"""
if anchor not in s: raise SystemExit('fit insertion anchor missing')
s=s.replace(anchor,helper+anchor,1)

old=r"""          if(rewardCost===null||have<pitCanonWhole(rewardCost)){
            const removed=config.steps.length-index;
            config.steps.splice(index);
            progress.total=Math.max(progress.done,progress.total-removed);
            hkRunner.setStep(`${pitCanonDefinitionName(def)} · ${either('турнирный план остановлен — не хватает Пропусков Ямы','reward plan stopped — not enough Pit Passes')}`,progress.done,progress.total);
            pitCanonRunnerLog(`${pitCanonDefinitionName(def)} — ${either('турнирный план безопасно остановлен: фактических Пропусков Ямы недостаточно','reward plan stopped safely: actual Pit Pass balance is insufficient')}`,'warn');
            break;
          }
"""
new=r"""          if(rewardCost===null||have<pitCanonWhole(rewardCost)){
            const fitted=pitCanonFitRewardStepToAvailable(config,index,have);
            if(fitted.changed){
              progress.total=Math.max(progress.done,progress.total+fitted.deltaRounds);
              step=config.steps[index];chunk=pitCanonWhole(step.chunk);
              rewardCost=pitCanonDirectPassCost(state,chunk,'ITEM');
              hkRunner.setStep(`${pitCanonDefinitionName(def)} · ${either('reward-шаг адаптирован','reward step adapted')} ×${fitted.before} → ×${fitted.after}`,progress.done,progress.total);
              pitCanonRunnerLog(`${pitCanonDefinitionName(def)} — ${either('reward-шаг адаптирован под доступные Пропуски Ямы','reward step adapted to available Pit Passes')}: ×${fitted.before} → ${fitted.replacement.map(value=>'×'+value).join(' + ')}`,'info');
            }
          }
          if(rewardCost===null||have<pitCanonWhole(rewardCost)){
            const removed=config.steps.length-index;
            config.steps.splice(index);
            progress.total=Math.max(progress.done,progress.total-removed);
            hkRunner.setStep(`${pitCanonDefinitionName(def)} · ${either('турнирный план остановлен — не хватает Пропусков Ямы','reward plan stopped — not enough Pit Passes')}`,progress.done,progress.total);
            pitCanonRunnerLog(`${pitCanonDefinitionName(def)} — ${either('турнирный план безопасно остановлен: фактических Пропусков Ямы недостаточно','reward plan stopped safely: actual Pit Pass balance is insufficient')}`,'warn');
            break;
          }
"""
old=old.replaceAll('`',chr(96)).replaceAll('§'+chr(123),'$'+chr(123))
new=new.replaceAll('`',chr(96)).replaceAll('§'+chr(123),'$'+chr(123))
if old not in s: raise SystemExit('reward insufficient block missing')
s=s.replace(old,new,1)

for needle in [
    MARK,
    "function pitCanonFitRewardStepToAvailable(config,index,availablePasses)",
    "reward step adapted",
    "config.steps.splice(index,1,...replacement)",
    "config.itemPassBudget=Math.max"
]:
    if needle not in s: raise SystemExit('missing r18 invariant: '+needle)

p.write_text(s,encoding='utf-8')
print('PITS_REWARD_FIT_R18_PATCH_OK')
