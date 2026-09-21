from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")
original=s

required=[
    "// @version      1.17.15",
    "const BUILD_VERSION = '1.17.15';",
    "const HK_CORE_REVISION = 'core-20260921-r17-buildings-ui-compact';",
    "const HK_BUILDINGS_CANON_REV = 'buildings-canon-core-20260920-r1';",
    "const HK_BUILDINGS_UI_REV = 'buildings-ui-20260921-r3';",
    "function buildingCanonActiveRows(documentValue=playerDocument)",
    "async function runBuildingsCanonical()",
    "maps-shared-runtime-20260921-r7-safe5",
    "explore-e3-single-20260920-r9-runner",
    "AUTH_PASSIVE_SAFETY_R1",
]
for marker in required:
    if marker not in s:
        raise SystemExit(f"missing expected marker: {marker}")

s=s.replace("// @version      1.17.15","// @version      1.17.16",1)
s=s.replace(
    "// @release-note На экране «Здания» убран лишний перечень всех активных зданий; оставлен только счётчик.",
    "// @release-note Исправлен расчёт активных зданий: план и запуск теперь используют реальные активные слоты игры.\n"
    "// @release-note На экране «Здания» убран лишний перечень всех активных зданий; оставлен только счётчик.",
    1,
)
s=s.replace("const BUILD_VERSION = '1.17.15';","const BUILD_VERSION = '1.17.16';",1)
s=s.replace(
    "const HK_CORE_REVISION = 'core-20260921-r17-buildings-ui-compact';",
    "const HK_CORE_REVISION = 'core-20260921-r18-buildings-active-fix';",
    1,
)
s=s.replace(
    "const HK_BUILDINGS_UI_REV = 'buildings-ui-20260921-r3';",
    "const HK_BUILDINGS_UI_REV = 'buildings-ui-20260921-r3';\n"
    "  const HK_BUILDINGS_ACTIVE_REV = 'buildings-active-semantics-20260921-r1';",
    1,
)

old_block=r'''  function buildingCanonActiveRows(documentValue=playerDocument) {
    const state=documentValue||{};
    const rows=Array.isArray(state?.buildings)?state.buildings:(Array.isArray(state?.player?.buildings)?state.player.buildings:[]);
    return rows.filter(row=>row&&String(row?.id||row?.building_id||''));
  }

  function buildingCanonActiveIds(documentValue=playerDocument) {
    return new Set(buildingCanonActiveRows(documentValue).map(row=>String(row?.id||row?.building_id||'')));
  }

  function buildingCanonCapacity(documentValue=playerDocument) {
    const state=documentValue||{},player=state?.player||{};
    const active=buildingCanonActiveRows(state);
    const maxRaw=player?.max_buildings??state?.max_buildings;
    const max=Number.isFinite(Number(maxRaw))&&Number(maxRaw)>=0?Math.trunc(Number(maxRaw)):null;
    const favoriteRows=active.filter(row=>row?.is_favorite===true||row?.favorite===true);
    const favoriteMaxRaw=player?.max_favorite_building??state?.max_favorite_building;
    const favoriteMax=Number.isFinite(Number(favoriteMaxRaw))&&Number(favoriteMaxRaw)>=0?Math.trunc(Number(favoriteMaxRaw)):null;
    return {
      active:active.length,
      max,
      free:max===null?null:Math.max(0,max-active.length),
      favorites:favoriteRows.length,
      favoriteMax,
      favoriteFree:favoriteMax===null?null:Math.max(0,favoriteMax-favoriteRows.length)
    };
  }
'''
new_block=r'''  function buildingCanonAllRows(documentValue=playerDocument) {
    const state=documentValue||{};
    const rows=Array.isArray(state?.buildings)?state.buildings:(Array.isArray(state?.player?.buildings)?state.player.buildings:[]);
    return rows.filter(row=>row&&String(row?.id||row?.building_id||''));
  }

  function buildingCanonReportedActiveCount(documentValue=playerDocument) {
    const state=documentValue||{},player=state?.player||{};
    const raw=player?.player_active_building??state?.player_active_building;
    const value=Number(raw);
    return Number.isFinite(value)&&value>=0?Math.trunc(value):null;
  }

  function buildingCanonActiveRows(documentValue=playerDocument) {
    const rows=buildingCanonAllRows(documentValue);
    const reported=buildingCanonReportedActiveCount(documentValue);
    // Current /player/me schema keeps every known building in `buildings`.
    // Only active rows have a numeric next_tier_level. The game also exposes
    // player_active_building; require both signals to agree before trusting the
    // row-level active set. If schema drifts, fail closed for ID exclusion.
    const flagged=rows.filter(row=>row?.next_tier_level!==null&&row?.next_tier_level!==undefined&&Number.isFinite(Number(row.next_tier_level)));
    if(reported!==null&&flagged.length===reported)return flagged;
    if(reported===null&&flagged.length)return flagged;
    return rows;
  }

  function buildingCanonActiveIds(documentValue=playerDocument) {
    return new Set(buildingCanonActiveRows(documentValue).map(row=>String(row?.id||row?.building_id||'')));
  }

  function buildingCanonCapacity(documentValue=playerDocument) {
    const state=documentValue||{},player=state?.player||{};
    const allRows=buildingCanonAllRows(state);
    const activeRows=buildingCanonActiveRows(state);
    const reportedActive=buildingCanonReportedActiveCount(state);
    const active=reportedActive===null?activeRows.length:reportedActive;
    const maxRaw=player?.max_buildings??state?.max_buildings;
    const max=Number.isFinite(Number(maxRaw))&&Number(maxRaw)>=0?Math.trunc(Number(maxRaw)):null;
    const favoriteRows=allRows.filter(row=>row?.is_favorite===true||row?.favorite===true);
    const favoriteMaxRaw=player?.max_favorite_building??state?.max_favorite_building;
    const favoriteMax=Number.isFinite(Number(favoriteMaxRaw))&&Number(favoriteMaxRaw)>=0?Math.trunc(Number(favoriteMaxRaw)):null;
    return {
      active,
      max,
      free:max===null?null:Math.max(0,max-active),
      favorites:favoriteRows.length,
      favoriteMax,
      favoriteFree:favoriteMax===null?null:Math.max(0,favoriteMax-favoriteRows.length)
    };
  }
'''
if old_block not in s:
    raise SystemExit("active/capacity block not found")
s=s.replace(old_block,new_block,1)

old_run=r'''      const capacity=buildingCanonPlan.capacity;
      const source=buildingCanonPlan.candidates;
      const candidates=capacity.free===null?source:source.slice(0,capacity.free);
      if(!candidates.length){log(either('Подходящих неоткрытых зданий нет.','No eligible unopened buildings.'),'warn');return;}
'''
new_run=r'''      const capacity=buildingCanonPlan.capacity;
      const source=buildingCanonPlan.candidates;
      if(!source.length){log(either('Подходящих неактивных зданий нет.','No eligible inactive buildings.'),'warn');return;}
      if(capacity.free!==null&&capacity.free<=0){log(either('Подходящие здания есть, но свободных активных слотов нет.','Eligible buildings exist, but there are no free active-building slots.'),'warn');return;}
      const candidates=capacity.free===null?source:source.slice(0,capacity.free);
'''
if old_run not in s:
    raise SystemExit("runner capacity slice block not found")
s=s.replace(old_run,new_run,1)

checks=[
    "// @version      1.17.16",
    "const BUILD_VERSION = '1.17.16';",
    "core-20260921-r18-buildings-active-fix",
    "buildings-active-semantics-20260921-r1",
    "player_active_building",
    "next_tier_level",
    "Подходящие здания есть, но свободных активных слотов нет.",
    "maps-shared-runtime-20260921-r7-safe5",
    "explore-e3-single-20260920-r9-runner",
    "const HK_MAP_READ_CONCURRENCY = 5;",
    "AUTH_PASSIVE_SAFETY_R1",
]
for marker in checks:
    if marker not in s:
        raise SystemExit(f"post-patch marker missing: {marker}")

# Guard unrelated canonical action logic around actual opening/favorite/rereads.
for marker in [
    "hkMutationGate.run('/player/building'",
    "buildingCanonOpen(candidate.buildingId)",
    "buildingCanonFavorite(candidate.buildingId)",
    "hkAuthoritativePlayerRead('buildings:before-open')",
    "hkAuthoritativePlayerRead('buildings:after-open')",
    "hkAuthoritativePlayerRead('buildings:complete')",
]:
    if marker not in s:
        raise SystemExit(f"Buildings action invariant lost: {marker}")

PATH.write_text(s,encoding="utf-8")
print("BUILDINGS_ACTIVE_SEMANTICS_R1_PATCH=PASS")
