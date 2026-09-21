from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")

required=[
    "// @version      1.17.17",
    "const BUILD_VERSION = '1.17.17';",
    "const HK_CORE_REVISION = 'core-20260921-r19-buildings-limit-runner';",
    "const HK_BUILDINGS_ACTIVE_REV = 'buildings-active-semantics-20260921-r1';",
    "function buildingCanonAllRows(documentValue=playerDocument)",
    "function buildingCanonActiveRows(documentValue=playerDocument)",
    "async function runBuildingsCanonical()",
]
for marker in required:
    if marker not in s:
        raise SystemExit(f"missing expected marker: {marker}")

s=s.replace("// @version      1.17.17","// @version      1.17.18",1)
s=s.replace(
    "// @release-note Добавлен лимит открытия зданий: 1 / 10 / 15 / 20 / все доступные.",
    "// @release-note Исправлено открытие зданий: кандидаты теперь исключают все уже полученные здания, а успех проверяется по /player/me.\n"
    "// @release-note Избранное теперь подтверждается повторным чтением состояния, без ложного сообщения об успехе.\n"
    "// @release-note Добавлен лимит открытия зданий: 1 / 10 / 15 / 20 / все доступные.",
    1,
)
s=s.replace("const BUILD_VERSION = '1.17.17';","const BUILD_VERSION = '1.17.18';",1)
s=s.replace(
    "const HK_CORE_REVISION = 'core-20260921-r19-buildings-limit-runner';",
    "const HK_CORE_REVISION = 'core-20260921-r20-buildings-owned-postcondition';",
    1,
)
s=s.replace(
    "const HK_BUILDINGS_RUNNER_UI_REV = 'buildings-runner-ui-20260921-r1';",
    "const HK_BUILDINGS_RUNNER_UI_REV = 'buildings-runner-ui-20260921-r1';\n"
    "  const HK_BUILDINGS_OWNED_REV = 'buildings-owned-semantics-20260921-r1';\n"
    "  const HK_BUILDINGS_POSTCONDITION_REV = 'buildings-postcondition-20260921-r1';",
    1,
)

owned_anchor="""  function buildingCanonReportedActiveCount(documentValue=playerDocument) {
"""
owned_helpers="""  function buildingCanonOwnedIds(documentValue=playerDocument) {
    return new Set(buildingCanonAllRows(documentValue).map(row=>String(row?.id||row?.building_id||'')).filter(Boolean));
  }

  function buildingCanonOwnedRow(buildingId,documentValue=playerDocument) {
    const id=String(buildingId||'');
    return buildingCanonAllRows(documentValue).find(row=>String(row?.id||row?.building_id||'')===id)||null;
  }

  function buildingCanonIsFavorite(buildingId,documentValue=playerDocument) {
    const row=buildingCanonOwnedRow(buildingId,documentValue);
    return !!(row&&(row?.is_favorite===true||row?.favorite===true||row?.slot_index!==null&&row?.slot_index!==undefined));
  }

  function buildingCanonReportedActiveCount(documentValue=playerDocument) {
"""
if owned_anchor not in s:
    raise SystemExit("owned helper anchor missing")
s=s.replace(owned_anchor,owned_helpers,1)

old_plan="""    const settings=buildingCanonSettings();
    const owned=(playerDocument?.areas?.areas||[]).filter(row=>row?.gamearea_id||row?.area_id);
    const active=buildingCanonActiveIds(playerDocument);
    const seen=new Set(),candidates=[];
"""
new_plan="""    const settings=buildingCanonSettings();
    const owned=(playerDocument?.areas?.areas||[]).filter(row=>row?.gamearea_id||row?.area_id);
    const ownedBuildingIds=buildingCanonOwnedIds(playerDocument);
    const seen=new Set(),candidates=[];
"""
if old_plan not in s:
    raise SystemExit("plan owned/active anchor missing")
s=s.replace(old_plan,new_plan,1)
s=s.replace(
    "if(!buildingId||active.has(buildingId)||seen.has(buildingId))continue;",
    "if(!buildingId||ownedBuildingIds.has(buildingId)||seen.has(buildingId))continue;",
    1,
)

# Add favorite slots to the visible plan.
old_stats="""          '<div class="hk-building-stat"><span>'+either('Активные','Active')+'</span><b>'+activeValue+'</b></div>'+
          '<div class="hk-building-stat"><span>'+either('Карты районов','Mapped districts')+'</span><b>'+plan.mappedAreas+'/'+plan.ownedAreas+'</b></div>'+
"""
new_stats="""          '<div class="hk-building-stat"><span>'+either('Активные','Active')+'</span><b>'+activeValue+'</b></div>'+
          '<div class="hk-building-stat"><span>'+either('Избранное','Favorites')+'</span><b>'+capacity.favorites+(capacity.favoriteMax===null?'':'/'+capacity.favoriteMax)+'</b></div>'+
          '<div class="hk-building-stat"><span>'+either('Карты районов','Mapped districts')+'</span><b>'+plan.mappedAreas+'/'+plan.ownedAreas+'</b></div>'+
"""
if old_stats not in s:
    raise SystemExit("stats anchor missing")
s=s.replace(old_stats,new_stats,1)
s=s.replace(
    ".hk-building-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;margin-bottom:9px}",
    ".hk-building-stats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:7px;margin-bottom:9px}",
    1,
)

old_precheck="""        playerDocument=await hkAuthoritativePlayerRead('buildings:before-open');
        if(buildingCanonActiveIds(playerDocument).has(candidate.buildingId)){
          done+=1;hkRunner.setStep(either('Уже открыто — пропуск','Already open — skipped'),done,candidates.length);continue;
        }
        const liveCapacity=buildingCanonCapacity(playerDocument);
"""
new_precheck="""        playerDocument=await hkAuthoritativePlayerRead('buildings:before-open');
        if(buildingCanonOwnedIds(playerDocument).has(candidate.buildingId)){
          done+=1;hkRunner.setStep(either('Уже получено — пропуск','Already owned — skipped'),done,candidates.length);continue;
        }
        const beforeCapacity=buildingCanonCapacity(playerDocument);
        const liveCapacity=beforeCapacity;
"""
if old_precheck not in s:
    raise SystemExit("pre-open check block missing")
s=s.replace(old_precheck,new_precheck,1)

old_success="""        opened+=1;
        try{buildingStudyCache.set(candidate.buildingId,result);await acceptBuildingStudy((apiBase||GAME_API_FALLBACK)+'/player/building?building_id='+encodeURIComponent(candidate.buildingId),apiHeaders,result);}catch(_){}
        const metrics=buildingCanonActualMetrics(result,candidate);
        log(`✓ ${candidate.buildingId} · 💎 ${metrics.crystals} · ${either('событий','events')} ${metrics.totalEvents}`,'ok');
        if(favoriteEnabled&&metrics.crystals>=buildingCanonPlan.settings.favoriteFrom){
          const favCap=buildingCanonCapacity(playerDocument);
          if(favCap.favoriteFree!==null&&favCap.favoriteFree<=0){favoriteEnabled=false;log(either('Свободных мест в избранном больше нет.','No favorite slots remain.'),'warn');}
          else{
            try{await buildingCanonFavorite(candidate.buildingId);favorites+=1;log(`★ ${candidate.buildingId} · ${either('добавлено в избранное','added to favorites')}`,'ok');}
            catch(error){if(buildingCanonFavoriteFullError(error)){favoriteEnabled=false;log(either('Лимит избранных зданий достигнут.','Favorite building limit reached.'),'warn');}else log(`↷ ${candidate.buildingId} · ${either('не удалось добавить в избранное','favorite failed')}: ${error?.message||error}`,'warn');}
          }
        }
        done+=1;hkRunner.setStep(candidate.buildingId,done,candidates.length);
        playerDocument=await hkAuthoritativePlayerRead('buildings:after-open');
"""
new_success="""        try{buildingStudyCache.set(candidate.buildingId,result);await acceptBuildingStudy((apiBase||GAME_API_FALLBACK)+'/player/building?building_id='+encodeURIComponent(candidate.buildingId),apiHeaders,result);}catch(_){}

        let claimed=false;
        for(let verifyAttempt=0;verifyAttempt<3;verifyAttempt+=1){
          playerDocument=await hkAuthoritativePlayerRead('buildings:after-claim');
          if(buildingCanonOwnedIds(playerDocument).has(candidate.buildingId)){claimed=true;break;}
          if(verifyAttempt<2)await gameRetryDelay(700*(verifyAttempt+1));
        }
        if(!claimed){
          errors+=1;done+=1;
          log(`✗ ${candidate.buildingId} · ${either('сервер не подтвердил получение здания','server did not confirm building claim')}`,'bad');
          hkRunner.setStep(either('Не подтверждено','Not confirmed'),done,candidates.length);
          continue;
        }

        const afterCapacity=buildingCanonCapacity(playerDocument);
        opened+=1;
        const metrics=buildingCanonActualMetrics(result,candidate);
        const activeDelta=beforeCapacity.active!==null&&afterCapacity.active!==null?afterCapacity.active-beforeCapacity.active:null;
        log(`✓ ${candidate.buildingId} · 💎 ${metrics.crystals}${activeDelta===null?'':` · Δactive ${activeDelta>=0?'+':''}${activeDelta}`}`,'ok');

        if(favoriteEnabled&&metrics.crystals>=buildingCanonPlan.settings.favoriteFrom){
          const favCap=buildingCanonCapacity(playerDocument);
          if(favCap.favoriteFree!==null&&favCap.favoriteFree<=0){
            favoriteEnabled=false;log(either('Свободных мест в избранном больше нет.','No favorite slots remain.'),'warn');
          }else{
            try{
              await buildingCanonFavorite(candidate.buildingId);
              let favoriteConfirmed=false;
              for(let favAttempt=0;favAttempt<3;favAttempt+=1){
                playerDocument=await hkAuthoritativePlayerRead('buildings:after-favorite');
                if(buildingCanonIsFavorite(candidate.buildingId,playerDocument)){favoriteConfirmed=true;break;}
                if(favAttempt<2)await gameRetryDelay(500*(favAttempt+1));
              }
              if(favoriteConfirmed){
                favorites+=1;log(`★ ${candidate.buildingId} · ${either('избранное подтверждено','favorite confirmed')}`,'ok');
              }else{
                errors+=1;log(`↷ ${candidate.buildingId} · ${either('сервер не подтвердил добавление в избранное','server did not confirm favorite')}`,'warn');
              }
            }catch(error){
              if(buildingCanonFavoriteFullError(error)){favoriteEnabled=false;log(either('Лимит избранных зданий достигнут.','Favorite building limit reached.'),'warn');}
              else{errors+=1;log(`↷ ${candidate.buildingId} · ${either('не удалось добавить в избранное','favorite failed')}: ${error?.message||error}`,'warn');}
            }
          }
        }
        done+=1;hkRunner.setStep(candidate.buildingId,done,candidates.length);
        playerDocument=await hkAuthoritativePlayerRead('buildings:after-open');
"""
if old_success not in s:
    raise SystemExit("optimistic success block missing")
s=s.replace(old_success,new_success,1)

s=s.replace(
    "if(!source.length){log(either('Подходящих неактивных зданий нет.','No eligible inactive buildings.'),'warn');return;}",
    "if(!source.length){log(either('Подходящих неоткрытых зданий нет.','No eligible unowned buildings.'),'warn');return;}",
    1,
)

for marker in [
    "// @version      1.17.18",
    "const BUILD_VERSION = '1.17.18';",
    "core-20260921-r20-buildings-owned-postcondition",
    "buildings-owned-semantics-20260921-r1",
    "buildings-postcondition-20260921-r1",
    "function buildingCanonOwnedIds(",
    "function buildingCanonIsFavorite(",
    "ownedBuildingIds.has(buildingId)",
    "buildingCanonOwnedIds(playerDocument).has(candidate.buildingId)",
    "server did not confirm building claim",
    "favorite confirmed",
    "server did not confirm favorite",
    "either('Избранное','Favorites')",
    "maps-shared-runtime-20260921-r7-safe5",
    "explore-e3-single-20260920-r9-runner",
    "AUTH_PASSIVE_SAFETY_R1",
]:
    if marker not in s:
        raise SystemExit(f"post-patch marker missing: {marker}")

# Keep Explore on active-row semantics; Buildings gets separate owned semantics.
explore_start=s.index("function exploreActive(")
explore_end=s.index("function exploreTotalEvents",explore_start)
if "buildingCanonActiveRows(st)" not in s[explore_start:explore_end]:
    raise SystemExit("Explore active semantics changed unexpectedly")

PATH.write_text(s,encoding="utf-8")
print("BUILDINGS_OWNED_POSTCONDITION_R1_PATCH=PASS")
