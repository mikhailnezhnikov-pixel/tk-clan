from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")

required=[
    "// @version      1.17.18",
    "const BUILD_VERSION = '1.17.18';",
    "const HK_CORE_REVISION = 'core-20260921-r20-buildings-owned-postcondition';",
    "const HK_BUILDINGS_POSTCONDITION_REV = 'buildings-postcondition-20260921-r1';",
    "const hkGameBridge = (() => {",
    "async function runBuildingsCanonical()",
]
for marker in required:
    if marker not in s:
        raise SystemExit(f"missing expected marker: {marker}")

s=s.replace("// @version      1.17.18","// @version      1.17.19",1)
s=s.replace(
    "// @release-note Исправлено открытие зданий: кандидаты теперь исключают все уже полученные здания, а успех проверяется по /player/me.",
    "// @release-note После открытия зданий HK теперь проверяет native-store игры и синхронизирует карту; при необходимости выполняется одна безопасная перезагрузка.\n"
    "// @release-note Исправлено открытие зданий: кандидаты теперь исключают все уже полученные здания, а успех проверяется по /player/me.",
    1,
)
s=s.replace("const BUILD_VERSION = '1.17.18';","const BUILD_VERSION = '1.17.19';",1)
s=s.replace(
    "const HK_CORE_REVISION = 'core-20260921-r20-buildings-owned-postcondition';",
    "const HK_CORE_REVISION = 'core-20260921-r21-buildings-native-sync';",
    1,
)
s=s.replace(
    "const HK_BUILDINGS_POSTCONDITION_REV = 'buildings-postcondition-20260921-r1';",
    "const HK_BUILDINGS_POSTCONDITION_REV = 'buildings-postcondition-20260921-r1';\n"
    "  const HK_BUILDINGS_NATIVE_SYNC_REV = 'buildings-native-sync-20260921-r1';",
    1,
)

bridge_anchor="""    const summary = () => ({ready:ready(),dirty,flushing,lastDiscoveryAt,lastFlushAt,discoveries,flushes,failures,hasGeneralViewStore:!!generalViewStore});
    return {discover,flush,schedule,noteMutation,summary,get ready(){return ready();},get dirty(){return dirty;}};
"""
bridge_new="""    const buildingState = buildingId => {
      const id=String(buildingId||'');
      if(!id)return {known:false,owned:null,favorite:null};
      try{
        if(!ready())discover(false);
        const store=player?.buildings?.$;
        if(!store||typeof store.has!=='function')return {known:false,owned:null,favorite:null};
        const owned=store.has(id);
        const row=owned&&typeof store.get==='function'?store.get(id):null;
        const favorite=owned?!!(row&&row.favoriteSlot!==undefined&&row.favoriteSlot!==null):false;
        return {known:true,owned,favorite};
      }catch(_){return {known:false,owned:null,favorite:null};}
    };
    const summary = () => ({ready:ready(),dirty,flushing,lastDiscoveryAt,lastFlushAt,discoveries,flushes,failures,hasGeneralViewStore:!!generalViewStore});
    return {discover,flush,schedule,noteMutation,summary,buildingState,get ready(){return ready();},get dirty(){return dirty;}};
"""
if bridge_anchor not in s:
    raise SystemExit("game bridge return anchor missing")
s=s.replace(bridge_anchor,bridge_new,1)

s=s.replace(
    "let opened=0,favorites=0,errors=0,capacityStopped=false,favoriteEnabled=true;",
    "let opened=0,favorites=0,errors=0,capacityStopped=false,favoriteEnabled=true;\n    const openedIds=[],favoriteIds=[];",
    1,
)
s=s.replace(
    "opened+=1;\n        const metrics=buildingCanonActualMetrics(result,candidate);",
    "opened+=1;openedIds.push(candidate.buildingId);\n        const metrics=buildingCanonActualMetrics(result,candidate);",
    1,
)
s=s.replace(
    "favorites+=1;log(`★ ${candidate.buildingId} · ${either('избранное подтверждено','favorite confirmed')}`,'ok');",
    "favorites+=1;favoriteIds.push(candidate.buildingId);log(`★ ${candidate.buildingId} · ${either('избранное подтверждено','favorite confirmed')}`,'ok');",
    1,
)

old_finish="""      playerDocument=await hkAuthoritativePlayerRead('buildings:complete');
      buildingCanonPlan=await buildingCanonBuildPlan(false);
      renderBuildings();
      hkRunner.finish(either('Открытие зданий завершено','Building opening completed'));
      log(either(
"""
new_finish="""      playerDocument=await hkAuthoritativePlayerRead('buildings:complete');
      buildingCanonPlan=await buildingCanonBuildPlan(false);
      renderBuildings();

      if(openedIds.length||favoriteIds.length){
        hkRunner.setStep(either('Синхронизация игры','Syncing game'),done,candidates.length);
        const bridgeOk=await hkGameBridge.flush(true);
        let nativeConfirmed=bridgeOk;
        if(nativeConfirmed){
          for(const id of openedIds){
            const state=hkGameBridge.buildingState(id);
            if(!state.known||state.owned!==true){nativeConfirmed=false;break;}
          }
        }
        if(nativeConfirmed){
          for(const id of favoriteIds){
            const state=hkGameBridge.buildingState(id);
            if(!state.known||state.favorite!==true){nativeConfirmed=false;break;}
          }
        }
        if(!nativeConfirmed){
          log(either(
            'Сервер подтвердил изменения, но интерфейс игры не синхронизировался. Выполняю одно обновление игры.',
            'Server confirmed the changes, but the game UI did not sync. Reloading the game once.'
          ),'warn');
          showVisualNotice(
            either('Синхронизация зданий','Building sync'),
            either('Изменения сохранены. Игра обновится один раз, чтобы карта увидела новые здания.','Changes are saved. The game will reload once so the map sees the new buildings.')
          );
          setTimeout(()=>location.reload(),900);
          return;
        }
        log(either('Карта игры синхронизирована с новыми зданиями.','Game map synced with the new buildings.'),'ok');
      }

      hkRunner.finish(either('Открытие зданий завершено','Building opening completed'));
      log(either(
"""
if old_finish not in s:
    raise SystemExit("Buildings finish block missing")
s=s.replace(old_finish,new_finish,1)

for marker in [
    "// @version      1.17.19",
    "const BUILD_VERSION = '1.17.19';",
    "core-20260921-r21-buildings-native-sync",
    "buildings-native-sync-20260921-r1",
    "const buildingState = buildingId =>",
    "hkGameBridge.buildingState(id)",
    "const bridgeOk=await hkGameBridge.flush(true);",
    "Сервер подтвердил изменения, но интерфейс игры не синхронизировался.",
    "setTimeout(()=>location.reload(),900);",
    "Карта игры синхронизирована с новыми зданиями.",
    "maps-shared-runtime-20260921-r7-safe5",
    "explore-e3-single-20260920-r9-runner",
    "AUTH_PASSIVE_SAFETY_R1",
]:
    if marker not in s:
        raise SystemExit(f"post-patch marker missing: {marker}")

PATH.write_text(s,encoding="utf-8")
print("BUILDINGS_NATIVE_SYNC_R1_PATCH=PASS")
