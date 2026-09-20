from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')
BASE="const HK_PITS_REWARD_EXEC_REV = 'pits-reward-execution-20260920-r13';"
MARK="const HK_PITS_SUMMARY_REV = 'pits-plan-totals-20260920-r14';"
if MARK in s: raise SystemExit('already applied')
if BASE not in s: raise SystemExit('r13 marker missing')
s=s.replace(BASE,BASE+"\n  "+MARK,1)

anchor="  function pitCanonRunnerLog(message,type='') { log(message,type); hkRunner.note(message,type); }\n"
helper="""  function pitCanonModeLabel(config){
    return config?.resume?either('Продолжить активную Яму','Continue active Pit'):(config?.sniper?either('Режим снайпера','Sniper mode'):either('Обычный','Normal'));
  }
  function pitCanonLogPlan(configs){
    const rounds=configs.reduce((n,c)=>n+(c.steps?.length||0),0);
    const crystals=configs.reduce((n,c)=>n+pitCanonWhole(c.crystalBudget),0);
    const passes=configs.reduce((n,c)=>n+pitCanonWhole(c.itemPassBudget),0);
    const paws=configs.reduce((n,c)=>n+(pitCanonWhole(c.maxRestoration)*(c.steps?.length||0)),0);
    pitCanonRunnerLog('━━ '+either('План выполнения','Execution plan')+' ━━','info');
    pitCanonRunnerLog(either('Выбранные Ямы','Selected Pits')+': '+configs.length+' · '+either('Всего раундов','Total rounds')+': '+rounds,'info');
    pitCanonRunnerLog(either('Максимальная стоимость','Maximum cost')+': 💎 '+crystals+' · 🎟 '+passes+' · 🐾 '+paws,'info');
    configs.forEach((c,i)=>pitCanonRunnerLog((i+1)+'. '+pitCanonDefinitionName(c.definition)+' · '+either('Старт','Start')+': '+pitCanonWhole(c.startLevel)+' · '+either('Режим','Mode')+': '+pitCanonModeLabel(c)+' · '+either('Раунды','Rounds')+': '+(c.steps||[]).map(x=>'×'+pitCanonWhole(x.chunk)).join(' + '),'info'));
  }
  function pitCanonLogTotals(config,stats){
    pitCanonRunnerLog('━━ '+pitCanonDefinitionName(config.definition)+' — '+either('Итоги Ямы','Pit totals')+' ━━','info');
    pitCanonRunnerLog(either('Режим','Mode')+': '+pitCanonModeLabel(config)+' · '+either('Раунды','Rounds')+': '+stats.rounds+'/'+(config.steps?.length||0)+' · '+either('Пропуски','Passes')+': '+stats.passesUsed+' · 💎 '+stats.crystals+' · 🎟 '+stats.itemPasses+' · 🐾 '+stats.restoration,'ok');
  }

"""
if anchor not in s: raise SystemExit('runner anchor missing')
s=s.replace(anchor,helper+anchor,1)

needle="      if(!base)return null;\n      if(reward.enabled&&reward.steps.length){\n"
replace="      if(!base)return null;\n      base.startLevel=pitCanonWhole(row.activeState?.level ?? row.state?.level);\n      if(reward.enabled&&reward.steps.length){\n"
if needle not in s: raise SystemExit('start level anchor missing')
s=s.replace(needle,replace,1)

start=s.index("  async function pitCanonRunOne(config,progress) {")
end=s.index("\n  async function runPitsCanonical()",start)
block=s[start:end]

needle="    let state=pitRaceSnapshot(def.id,playerDocument),spentCrystals=0,spentItems=0;\n"
replace=needle+"    const stats={rounds:0,passesUsed:0,crystals:0,itemPasses:0,restoration:0};\n"
if needle not in block: raise SystemExit('stats anchor missing')
block=block.replace(needle,replace,1)

needle="        spentCrystals+=pitCanonWhole(premCost);spentItems+=pitCanonWhole(itemCost);\n"
replace=needle+"        stats.passesUsed+=chunk;stats.crystals=spentCrystals;stats.itemPasses=spentItems;\n"
if needle not in block: raise SystemExit('spend stats anchor missing')
block=block.replace(needle,replace,1)

needle="          const respawnResponse=await apiJson(api.respawn,'POST',{payment_type:'ITEM'});restorationSpent+=cost;\n"
replace="          const respawnResponse=await apiJson(api.respawn,'POST',{payment_type:'ITEM'});restorationSpent+=cost;stats.restoration+=cost;\n"
if needle not in block: raise SystemExit('restoration stats anchor missing')
block=block.replace(needle,replace,1)

if "      if(leaveManual)return;\n" not in block: raise SystemExit('manual return anchor missing')
block=block.replace("      if(leaveManual)return;\n","      if(leaveManual)return stats;\n",1)

if "      progress.done+=1;" not in block: raise SystemExit('round counter anchor missing')
block=block.replace("      progress.done+=1;","      progress.done+=1;stats.rounds+=1;",1)

tail="      if(!config.autofinish)break;\n    }\n"
if tail not in block: raise SystemExit('return stats tail missing')
block=block.replace(tail,tail+"    stats.crystals=spentCrystals;stats.itemPasses=spentItems;\n    return stats;\n",1)
s=s[:start]+block+s[end:]

needle="    pitCanonDecisionBudgetReset();\n    pitCanonSetBusy(true);\n"
replace=needle+"    pitCanonLogPlan(configs);\n"
if needle not in s: raise SystemExit('plan call anchor missing')
s=s.replace(needle,replace,1)

needle="      for(const config of configs)await pitCanonRunOne(config,progress);\n"
replace="""      const totals={pits:0,rounds:0,passesUsed:0,crystals:0,itemPasses:0,restoration:0};
      for(const config of configs){
        const stats=await pitCanonRunOne(config,progress)||{rounds:0,passesUsed:0,crystals:0,itemPasses:0,restoration:0};
        totals.pits+=1;totals.rounds+=pitCanonWhole(stats.rounds);totals.passesUsed+=pitCanonWhole(stats.passesUsed);totals.crystals+=pitCanonWhole(stats.crystals);totals.itemPasses+=pitCanonWhole(stats.itemPasses);totals.restoration+=pitCanonWhole(stats.restoration);
        pitCanonLogTotals(config,stats);
      }
      pitCanonRunnerLog('━━ '+either('Итоги всех выбранных Ям','All selected Pits totals')+' ━━','info');
      pitCanonRunnerLog(either('Обработано Ям','Pits processed')+': '+totals.pits+'/'+configs.length+' · '+either('Раунды','Rounds')+': '+totals.rounds+'/'+progress.total+' · '+either('Пропуски','Passes')+': '+totals.passesUsed+' · 💎 '+totals.crystals+' · 🎟 '+totals.itemPasses+' · 🐾 '+totals.restoration,'ok');
"""
if needle not in s: raise SystemExit('aggregate anchor missing')
s=s.replace(needle,replace,1)

for x in [MARK,"function pitCanonLogPlan(configs)","function pitCanonLogTotals(config,stats)","stats.passesUsed+=chunk","stats.restoration+=cost","Итоги всех выбранных Ям"]:
    if x not in s: raise SystemExit('missing r14 invariant: '+x)
p.write_text(s,encoding='utf-8')
print('PITS_PLAN_TOTALS_R14_PATCH_OK')
