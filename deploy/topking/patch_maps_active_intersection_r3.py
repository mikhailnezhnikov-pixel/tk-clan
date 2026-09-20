from pathlib import Path

TARGET=Path('/tmp/HamsterKingMobile.user.js')
s=TARGET.read_text(encoding='utf-8')
OLD_REV="maps-building-scan-20260920-r2"
NEW_REV="maps-active-intersection-20260920-r3"

def require(needle,message):
    if needle not in s:
        raise SystemExit(message)

require(f"HK_MAP_SCANNER_REV = '{OLD_REV}'","scanner r2 missing")
require("HK_MAP_COORDS_REV = 'maps-coordinates-column-row-20260920-r1'","coords r1 missing")
require("HK_BUILDINGS_CANON_REV = 'buildings-canon-core-20260920-r1'","buildings r1 missing")

s=s.replace(f"HK_MAP_SCANNER_REV = '{OLD_REV}'",f"HK_MAP_SCANNER_REV = '{NEW_REV}'",1)

old_crystal="""  function crystalRoomCount(documentValue, ids = crystalEventIds()) {
    const direct=directCrystalRoomCount(documentValue);
    if (direct != null) return direct;
    const rooms=buildingRooms(documentValue);
    return rooms.length ? rooms.filter(room=>roomContainsCrystal(room,ids)).length : null;
  }
"""
new_crystal="""  function crystalRoomCount(documentValue, ids = crystalEventIds()) {
    const direct=directCrystalRoomCount(documentValue);
    if (direct != null) return direct;
    const rooms=buildingRooms(documentValue);
    if (!rooms.length) return null;
    const directMarked=rooms.filter(room=>containsCrystalMarker(room)).length;
    // Without /events we cannot safely translate bare event_id values.
    // Preserve known direct markers, but never turn an unavailable catalog
    // into a false zero.
    if (!ids?.size) return directMarked > 0 ? directMarked : null;
    return rooms.filter(room=>roomContainsCrystal(room,ids)).length;
  }

  async function ensureCrystalEventCatalog() {
    let ids=crystalEventIds();
    if (ids.size) return ids;
    try {
      eventCatalogDocument=normalizeEventCatalog(await apiJson('/events','GET'));
      ids=crystalEventIds();
    } catch (_) {}
    return ids;
  }

  function activePlayerBuildingIds(documentValue = hkStateStore.snapshot || playerDocument || {}) {
    return new Set((documentValue?.buildings || [])
      .map(row=>String(row?.id || row?.building_id || ''))
      .filter(Boolean));
  }
"""
require(old_crystal,"crystalRoomCount anchor missing")
s=s.replace(old_crystal,new_crystal,1)

old_backfill="""  async function mapBackfillActiveBuildingStudies(selectedAreaIds=null) {
    const state=hkStateStore.snapshot||playerDocument||{};
    const active=(state?.buildings||[]).map(row=>String(row?.id||row?.building_id||'')).filter(Boolean);
    const selected=selectedAreaIds instanceof Set?selectedAreaIds:null;
    const rows=[];
    for(const buildingId of active){
      const areaId=String(mapBuildingAreas.get(buildingId)||'');
      if(!areaId||(selected&&!selected.has(areaId)))continue;
      rows.push({buildingId,areaId});
    }
"""
new_backfill="""  async function mapBackfillActiveBuildingStudies(selectedAreaIds=null) {
    const state=hkStateStore.snapshot||playerDocument||{};
    const active=activePlayerBuildingIds(state);
    const selected=selectedAreaIds instanceof Set?selectedAreaIds:null;
    const crystalIds=await ensureCrystalEventCatalog();
    if(!crystalIds.size)log(either(
      'Каталог /events недоступен: здания без прямого crystal-маркера останутся неизвестными, ложный 0 не записывается.',
      '/events catalog is unavailable: buildings without a direct crystal marker stay unknown; false zero is not stored.'
    ),'warn');
    const rows=[];
    // Strict safe intersection:
    // building must be active in /player/me AND mapped by /game_area/{area}/buildings.
    for(const buildingId of active){
      const areaId=String(mapBuildingAreas.get(buildingId)||'');
      if(!areaId||(selected&&!selected.has(areaId)))continue;
      rows.push({buildingId,areaId});
    }
"""
require(old_backfill,"backfill anchor missing")
s=s.replace(old_backfill,new_backfill,1)

old_count="""          roomCount=crystalRoomCount(value);
"""
new_count="""          roomCount=crystalRoomCount(value,crystalIds);
"""
# Replace only the occurrence inside mapBackfill after its function start.
start=s.index("  async function mapBackfillActiveBuildingStudies")
pos=s.index(old_count,start)
s=s[:pos]+s[pos:].replace(old_count,new_count,1)

old_map="""    const playerBuildings = new Map((playerDocument?.buildings || []).map(row => [String(row?.id || ''), row]));
"""
new_map="""    const playerBuildings = new Map((playerDocument?.buildings || [])
      .map(row => [String(row?.id || row?.building_id || ''), row])
      .filter(([id]) => id));
"""
require(old_map,"mapAreaPayload player building map anchor missing")
s=s.replace(old_map,new_map,1)

# Explicitly keep /player/building read path and building opening mutation override separate.
require("'/player/building',","/player/building no longer classified read-only")
require("hkMutationGate.run('/player/building'","Buildings explicit opening gate missing")

# Invariants
require(f"HK_MAP_SCANNER_REV = '{NEW_REV}'","scanner r3 marker missing")
require("function activePlayerBuildingIds(","active building normalizer missing")
require("async function ensureCrystalEventCatalog()","crystal catalog guard missing")
require("row?.id || row?.building_id","building id fallback missing")
require("roomCount=crystalRoomCount(value,crystalIds)","backfill does not use verified event ids")
require("HK_MAP_COORDS_REV = 'maps-coordinates-column-row-20260920-r1'","coords invariant lost")
require("HK_BUILDINGS_CANON_REV = 'buildings-canon-core-20260920-r1'","buildings invariant lost")
require("HK_STAGE2J_BOSSES_REV = 'bosses-area-target-20260920-r2'","bosses invariant lost")
require("HK_PITS_REWARD_PICKER_REV = 'pits-reward-picker-20260920-r20'","pits invariant lost")

TARGET.write_text(s,encoding='utf-8')
