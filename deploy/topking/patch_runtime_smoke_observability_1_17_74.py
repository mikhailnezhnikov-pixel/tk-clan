from pathlib import Path

path = Path('/tmp/HamsterKingMobile.user.js')
s = path.read_text(encoding='utf-8')

def replace_once(old, new, label):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 match, got {count}')
    s = s.replace(old, new, 1)

replace_once(
    "// @version      1.17.73\n",
    "// @version      1.17.74\n// @release-note Диагностика smoke-test: Rat Hunt, War и Районы теперь пассивно записывают форму ответов и подтверждённое состояние после мутаций без дополнительных запросов к игре.\n",
    'metadata version'
)
replace_once(
    "const BUILD_VERSION = '1.17.73';",
    "const BUILD_VERSION = '1.17.74';",
    'build version'
)
replace_once(
    "  const HK_STAGE7_COMBAT_CONFIRM_REV = 'stage7-combat-confirm-20260923-r1';\n",
    "  const HK_STAGE7_COMBAT_CONFIRM_REV = 'stage7-combat-confirm-20260923-r1';\n"
    "  const HK_RUNTIME_SMOKE_OBSERVABILITY_REV = 'runtime-smoke-observability-20260923-r1';\n"
    "  function hkSmokeObjectKeys(value){\n"
    "    return value&&typeof value==='object'&&!Array.isArray(value)?Object.keys(value).slice(0,24):[];\n"
    "  }\n"
    "  function hkRuntimeSmokeRecord(type,data={}){\n"
    "    try{recordDiagnostic('runtime-smoke-'+type,{revision:HK_RUNTIME_SMOKE_OBSERVABILITY_REV,...data});}catch(_){}\n"
    "  }\n",
    'smoke marker/helper'
)

replace_once(
"""  function ratHuntAcceptResponse(response,reason='rat-hunt') {
    if(response&&typeof response==='object'){
      try{hkStateStore.merge(response,reason);}catch(_){}
      playerDocument=hkStateStore.snapshot||playerDocument;
      if(response?.pit_generals&&typeof response.pit_generals==='object'&&(!playerDocument||playerDocument.pit_generals!==response.pit_generals)){
        playerDocument={...(playerDocument||{}),pit_generals:response.pit_generals};
      }
    }
    ratHuntCombat.state=ratHuntCombatState(playerDocument)||ratHuntCombat.state;
    return response;
  }
""",
"""  function ratHuntAcceptResponse(response,reason='rat-hunt') {
    if(response&&typeof response==='object'){
      try{hkStateStore.merge(response,reason);}catch(_){}
      playerDocument=hkStateStore.snapshot||playerDocument;
      if(response?.pit_generals&&typeof response.pit_generals==='object'&&(!playerDocument||playerDocument.pit_generals!==response.pit_generals)){
        playerDocument={...(playerDocument||{}),pit_generals:response.pit_generals};
      }
    }
    ratHuntCombat.state=ratHuntCombatState(playerDocument)||ratHuntCombat.state;
    const smokeState=ratHuntCombat.state;
    hkRuntimeSmokeRecord('rat-hunt-state',{
      reason,
      responseKeys:hkSmokeObjectKeys(response),
      hasState:!!smokeState,
      isFinish:smokeState?.is_finish,
      level:Number(smokeState?.level??0),
      maxLevel:Number(smokeState?.max_preset_level??0),
      health:Number(smokeState?.health??0),
      massMultiplier:Number(smokeState?.mass_multiplier??0),
      passCosts:Array.isArray(smokeState?.pass_costs)?smokeState.pass_costs.length:0,
      respawnCosts:Array.isArray(smokeState?.respawn_costs)?smokeState.respawn_costs.length:0
    });
    return response;
  }
""",
    'rat accept'
)

replace_once(
"""  function warAcceptResponse(response,reason='war-combat') {
    if(response&&typeof response==='object'){
      try{hkStateStore.merge(response,reason);}catch(_){}
      playerDocument=hkStateStore.snapshot||playerDocument;
      if(response?.alliance_attack_war&&typeof response.alliance_attack_war==='object')warCombat.activeWar=response.alliance_attack_war;
    }
    return response;
  }
""",
"""  function warAcceptResponse(response,reason='war-combat') {
    if(response&&typeof response==='object'){
      try{hkStateStore.merge(response,reason);}catch(_){}
      playerDocument=hkStateStore.snapshot||playerDocument;
      if(response?.alliance_attack_war&&typeof response.alliance_attack_war==='object')warCombat.activeWar=response.alliance_attack_war;
    }
    const smokeWar=response?.alliance_attack_war||warCombat.activeWar||null;
    hkRuntimeSmokeRecord('war-state',{
      reason,
      responseKeys:hkSmokeObjectKeys(response),
      hasWar:!!smokeWar,
      health:Number(smokeWar?.health??0),
      initialHealth:Number(smokeWar?.initial_health??0),
      battleWin:response?.battle_result?.is_win===true?true:response?.battle_result?.is_win===false?false:null,
      previewRounds:Array.isArray(response?.pvp_preview?.rounds)?response.pvp_preview.rounds.length:0
    });
    return response;
  }
""",
    'war accept'
)

replace_once(
"""  function neighborhoodApplyIdler(data,reason='neighborhood') {
    const idler=data?.idler || data?.player?.idler || data?.data?.idler || data?.data?.player?.idler;
    if(!idler||typeof idler!=='object')return false;
    neighborhoodIdler=idler;
    try{
      hkStateStore.merge({idler,timestamp:data?.timestamp||data?.data?.timestamp},reason);
      playerDocument=hkStateStore.snapshot||playerDocument;
    }catch(_){}
    return true;
  }
""",
"""  function neighborhoodApplyIdler(data,reason='neighborhood') {
    const idler=data?.idler || data?.player?.idler || data?.data?.idler || data?.data?.player?.idler;
    if(!idler||typeof idler!=='object'){
      hkRuntimeSmokeRecord('neighborhood-shape-miss',{reason,responseKeys:hkSmokeObjectKeys(data)});
      return false;
    }
    neighborhoodIdler=idler;
    try{
      hkStateStore.merge({idler,timestamp:data?.timestamp||data?.data?.timestamp},reason);
      playerDocument=hkStateStore.snapshot||playerDocument;
    }catch(_){}
    const smokeBuildings=Array.isArray(idler?.buildings)?idler.buildings:[];
    hkRuntimeSmokeRecord('neighborhood-state',{
      reason,
      responseKeys:hkSmokeObjectKeys(data),
      tapPower:Number(idler?.player_tap_power??0),
      buildings:smokeBuildings.length,
      sample:smokeBuildings.slice(0,6).map(row=>({
        buildingId:String(row?.building_id||'').slice(0,80),
        level:Number(row?.level??0),
        maxLevel:Number(row?.max_level??row?.level??0),
        health:Number(row?.health??0)
      }))
    });
    return true;
  }
""",
    'neighborhood apply'
)

replace_once(
"""      playerDocument=await hkAuthoritativePlayerRead('rat-hunt:complete');
      await loadRatHuntCombat(false);
      hkRunner.finish(either('План Охоты на крыс завершён','Rat Hunt plan completed'));
""",
"""      playerDocument=await hkAuthoritativePlayerRead('rat-hunt:complete');
      await loadRatHuntCombat(false);
      hkRuntimeSmokeRecord('rat-hunt-complete',{
        hasState:!!ratHuntCombat.state,
        isFinish:ratHuntCombat.state?.is_finish,
        level:Number(ratHuntCombat.state?.level??0),
        health:Number(ratHuntCombat.state?.health??0)
      });
      hkRunner.finish(either('План Охоты на крыс завершён','Rat Hunt plan completed'));
""",
    'rat complete'
)
replace_once(
"""    }catch(error){
      try{playerDocument=await hkAuthoritativePlayerRead('rat-hunt:error');await loadRatHuntCombat(false);}catch(_){}
""",
"""    }catch(error){
      hkRuntimeSmokeRecord('rat-hunt-error',{
        name:String(error?.name||''),
        status:Number(error?.httpStatus||0),
        message:String(error?.message||error||'').slice(0,500)
      });
      try{playerDocument=await hkAuthoritativePlayerRead('rat-hunt:error');await loadRatHuntCombat(false);}catch(_){}
""",
    'rat error'
)

replace_once(
"""      const publicResult=await readPublicWar(warCombat.activeBattles);
      warSnapshot=publicResult?.war||null;warLastReadAt=Date.now();
      renderWars();
      hkRunner.finish(either('План войны завершён','War plan completed'));
""",
"""      const publicResult=await readPublicWar(warCombat.activeBattles);
      warSnapshot=publicResult?.war||null;warLastReadAt=Date.now();
      hkRuntimeSmokeRecord('war-complete',{
        hasWar:!!warCombat.activeWar,
        health:Number(warCombat.activeWar?.health??0),
        initialHealth:Number(warCombat.activeWar?.initial_health??0),
        passes:pitCanonResourceQuantity(playerDocument,WAR_FREE_PASS_ID,'currency')
      });
      renderWars();
      hkRunner.finish(either('План войны завершён','War plan completed'));
""",
    'war complete'
)
replace_once(
"""    }catch(error){
      try{
        playerDocument=await hkAuthoritativePlayerRead('wars:error');
""",
"""    }catch(error){
      hkRuntimeSmokeRecord('war-error',{
        name:String(error?.name||''),
        status:Number(error?.httpStatus||0),
        message:String(error?.message||error||'').slice(0,500)
      });
      try{
        playerDocument=await hkAuthoritativePlayerRead('wars:error');
""",
    'war error'
)

replace_once(
"""      progress();
      neighborhoodLastReadAt=Date.now();
      renderNeighborhoodBattles();
      hkRunner.finish(either('Все выбранные районы завершены','All selected Neighborhoods completed'));
""",
"""      progress();
      neighborhoodLastReadAt=Date.now();
      hkRuntimeSmokeRecord('neighborhood-complete',{
        tapPower:Number(neighborhoodIdler?.player_tap_power??0),
        buildings:Array.isArray(neighborhoodIdler?.buildings)?neighborhoodIdler.buildings.length:0
      });
      renderNeighborhoodBattles();
      hkRunner.finish(either('Все выбранные районы завершены','All selected Neighborhoods completed'));
""",
    'neighborhood complete'
)
replace_once(
"""    }catch(error){
      neighborhoodLastReadAt=Date.now();
      renderNeighborhoodBattles();
""",
"""    }catch(error){
      hkRuntimeSmokeRecord('neighborhood-error',{
        name:String(error?.name||''),
        status:Number(error?.httpStatus||0),
        message:String(error?.message||error||'').slice(0,500)
      });
      neighborhoodLastReadAt=Date.now();
      renderNeighborhoodBattles();
""",
    'neighborhood error'
)

if "runtime-smoke-observability-20260923-r1" not in s:
    raise SystemExit('smoke marker missing')
if "// @version      1.17.74" not in s or "const BUILD_VERSION = '1.17.74';" not in s:
    raise SystemExit('version patch failed')
if s.count("hkRuntimeSmokeRecord('rat-hunt-state'") != 1:
    raise SystemExit('rat smoke instrumentation mismatch')
if s.count("hkRuntimeSmokeRecord('war-state'") != 1:
    raise SystemExit('war smoke instrumentation mismatch')
if s.count("hkRuntimeSmokeRecord('neighborhood-state'") != 1:
    raise SystemExit('neighborhood smoke instrumentation mismatch')

path.write_text(s, encoding='utf-8')
print('PATCH_1_17_74_RUNTIME_SMOKE=PASS')
