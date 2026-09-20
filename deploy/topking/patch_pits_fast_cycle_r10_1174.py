from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')

BASE="const HK_PITS_RUNNER_HISTORY_REV = 'pits-runner-history-20260920-r9';"
MARK="const HK_PITS_SPEED_REV = 'pits-fast-cycle-20260920-r10';"
if MARK in s:
    raise SystemExit('already applied')
if BASE not in s:
    raise SystemExit('r9 marker missing')
s=s.replace(BASE, BASE+"\n  "+MARK, 1)

anchor="""  function pitCanonBattleTelemetry(def,level) {
"""
helper="""  function pitCanonFastCycleDelay(def,sniper=false) {
    if(sniper)return def?.id==='gang'?120:80;
    return def?.id==='gang'?180:120;
  }

  function pitCanonStateAfterMutation(def,response,reason) {
    playerDocument=hkStateStore.snapshot||playerDocument;
    let state=pitRaceSnapshot(def.id,playerDocument)||pitRaceSnapshot(def.id,response);
    return {state,needsReread:!state,reason};
  }

"""
if anchor not in s:
    raise SystemExit('telemetry anchor missing')
s=s.replace(anchor,helper+anchor,1)

old_resp="""          await apiJson(api.respawn,'POST',{payment_type:'ITEM'});restorationSpent+=cost;
          playerDocument=await hkAuthoritativePlayerRead(`pits:${def.id}:after-respawn`);state=pitRaceSnapshot(def.id,playerDocument);
          pitCanonRunnerLog(`✓ ${pitCanonDefinitionName(def)} — ${either('восстановлено','restored')} · HP ${pitCanonWhole(state?.health)} · 🐾 ${pitCanonResourceQuantity(playerDocument,HK_PIT_RESTORATION_ITEM_ID,'item')} ${either('осталось','remaining')}`,'ok');
          continue;
"""
new_resp="""          const respawnResponse=await apiJson(api.respawn,'POST',{payment_type:'ITEM'});restorationSpent+=cost;
          {
            const mutation=pitCanonStateAfterMutation(def,respawnResponse,`pits:${def.id}:after-respawn`);
            state=mutation.state;
            if(mutation.needsReread){playerDocument=await hkAuthoritativePlayerRead(mutation.reason);state=pitRaceSnapshot(def.id,playerDocument);}
          }
          pitCanonRunnerLog(`✓ ${pitCanonDefinitionName(def)} — ${either('восстановлено','restored')} · HP ${pitCanonWhole(state?.health)} · 🐾 ${pitCanonResourceQuantity(playerDocument,HK_PIT_RESTORATION_ITEM_ID,'item')} ${either('осталось','remaining')}`,'ok');
          await sleep(pitCanonFastCycleDelay(def,config.sniper));
          continue;
"""
if old_resp not in s:
    raise SystemExit('respawn block anchor missing')
s=s.replace(old_resp,new_resp,1)

old_battle="""        const battleResponse=await apiJson(api.battle,'POST');
        playerDocument=await hkAuthoritativePlayerRead(`pits:${def.id}:after-battle`);state=pitRaceSnapshot(def.id,playerDocument);
        const afterLevel=pitCanonWhole(state?.level);
"""
new_battle="""        const battleResponse=await apiJson(api.battle,'POST');
        {
          const mutation=pitCanonStateAfterMutation(def,battleResponse,`pits:${def.id}:after-battle`);
          state=mutation.state;
          if(mutation.needsReread){playerDocument=await hkAuthoritativePlayerRead(mutation.reason);state=pitRaceSnapshot(def.id,playerDocument);}
        }
        const afterLevel=pitCanonWhole(state?.level);
"""
if old_battle not in s:
    raise SystemExit('battle reread anchor missing')
s=s.replace(old_battle,new_battle,1)

old_log="""        pitCanonRunnerLog(`${won?'✓':'✗'} ${pitCanonDefinitionName(def)} — ${won?either('ПРОБИТО','WON'):either('НЕ ПРОБИТО','LOST')} · ${level} → ${level+1} · HP ${pitCanonWhole(state?.health)}${telemetry.chance!==null?` · ${either('шанс','chance')}: ${pitChanceLabel(telemetry.chance)}`:''}`,won?'ok':'warn');
"""
new_log=old_log+"        await sleep(pitCanonFastCycleDelay(def,config.sniper));\n"
if old_log not in s:
    raise SystemExit('battle log anchor missing')
s=s.replace(old_log,new_log,1)

for needle in [
    MARK,
    "function pitCanonFastCycleDelay(def,sniper=false)",
    "function pitCanonStateAfterMutation(def,response,reason)",
    "const respawnResponse=await apiJson(api.respawn",
    "const battleResponse=await apiJson(api.battle",
    "await sleep(pitCanonFastCycleDelay(def,config.sniper));"
]:
    if needle not in s:
        raise SystemExit('missing r10 invariant: '+needle)

p.write_text(s,encoding='utf-8')
print('PITS_FAST_CYCLE_R10_PATCH_OK')
