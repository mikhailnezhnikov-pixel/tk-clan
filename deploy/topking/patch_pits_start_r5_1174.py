from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')

BASE="const HK_PITS_TOOLBAR_REV = 'pits-toolbar-clean-20260920-r4';"
MARK="const HK_PITS_START_REV = 'pits-start-config-snapshot-20260920-r5';"
if MARK in s:
    raise SystemExit('already applied')
if BASE not in s:
    raise SystemExit('r4 marker missing')

s=s.replace(BASE, BASE+"\n  "+MARK, 1)

old="""  async function runPitsCanonical() {
    if(!requireLicense())return;if(hkRunner.running){alert(either('Сначала завершите текущую задачу','Finish the current task first'));return;}
    try{
      playerDocument=await hkAuthoritativePlayerRead('pits:prepare');pitCanonRender();const configs=pitCanonReadRunConfigs();if(!configs.length){alert(either('Выберите хотя бы одну Яму','Select at least one Pit'));return;}
      const total=configs.reduce((sum,row)=>sum+row.steps.length,0),progress={done:0,total};hkRunner.start({title:either('Ямы','Pits'),step:either('Подготовка','Preparing'),total,pausable:true,stoppable:true});
      for(const config of configs)await pitCanonRunOne(config,progress);
      playerDocument=await hkAuthoritativePlayerRead('pits:complete');pitCanonRender();hkRunner.finish(either('Ямы завершены','Pits completed'));log(either('Выбранные Ямы завершены.','Selected Pits completed.'),'ok');
    }catch(error){
"""
new="""  async function runPitsCanonical() {
    if(!requireLicense())return;if(hkRunner.running){alert(either('Сначала завершите текущую задачу','Finish the current task first'));return;}
    const configs=pitCanonReadRunConfigs();
    if(!configs.length){alert(either('Выберите хотя бы одну Яму','Select at least one Pit'));return;}
    const total=configs.reduce((sum,row)=>sum+row.steps.length,0),progress={done:0,total};
    hkRunner.start({title:either('Ямы','Pits'),step:either('Подготовка','Preparing'),total,pausable:true,stoppable:true});
    recordDiagnostic('pits-run-config-snapshot',{pits:configs.map(config=>({id:config.definition?.id,planId:config.planId,steps:config.steps?.length||0,sniper:!!config.sniper,target:config.target}))});
    try{
      playerDocument=await hkAuthoritativePlayerRead('pits:prepare');
      for(const config of configs)await pitCanonRunOne(config,progress);
      playerDocument=await hkAuthoritativePlayerRead('pits:complete');pitCanonRender();hkRunner.finish(either('Ямы завершены','Pits completed'));log(either('Выбранные Ямы завершены.','Selected Pits completed.'),'ok');
    }catch(error){
"""
if old not in s:
    raise SystemExit('runPitsCanonical anchor missing')
s=s.replace(old,new,1)

for needle in [
    MARK,
    "const configs=pitCanonReadRunConfigs();",
    "hkRunner.start({title:either('Ямы','Pits'),step:either('Подготовка','Preparing')",
    "recordDiagnostic('pits-run-config-snapshot'"
]:
    if needle not in s:
        raise SystemExit('missing invariant: '+needle)

bad="playerDocument=await hkAuthoritativePlayerRead('pits:prepare');pitCanonRender();const configs=pitCanonReadRunConfigs()"
if bad in s:
    raise SystemExit('old destructive pre-run order remains')

p.write_text(s,encoding='utf-8')
print('PITS_START_R5_PATCH_OK')
