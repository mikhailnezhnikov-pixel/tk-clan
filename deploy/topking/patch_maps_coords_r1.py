from pathlib import Path

TARGET=Path('/tmp/HamsterKingMobile.user.js')
s=TARGET.read_text(encoding='utf-8')
REV='maps-coordinates-column-row-20260920-r1'

def require(needle,message):
    if needle not in s:
        raise SystemExit(message)

require("HK_MAP_SCANNER_REV = 'maps-building-scan-20260920-r2'","Maps scanner r2 missing")
require("HK_BUILDINGS_CANON_REV = 'buildings-canon-core-20260920-r1'","Buildings r1 missing")

if f"HK_MAP_COORDS_REV = '{REV}'" not in s:
    marker="  const HK_MAP_SCANNER_REV = 'maps-building-scan-20260920-r2';"
    require(marker,"map scanner marker anchor missing")
    s=s.replace(marker,marker+f"\n  const HK_MAP_COORDS_REV = '{REV}';",1)

    runtime="  runtime.mapScannerStage = HK_MAP_SCANNER_REV;"
    require(runtime,"map scanner runtime anchor missing")
    s=s.replace(runtime,runtime+"\n  runtime.mapCoordsStage = HK_MAP_COORDS_REV;",1)

old="""    return {area_id:areaId, city_id:cityId, city_name:cityLabel(city), x:full?.info?.x ?? full?.meta?.gamearea_coords?.x,
      y:full?.info?.y ?? full?.meta?.gamearea_coords?.y, invest_count:Number(full?.info?.invest_count || invest.size),"""
new="""    // Game API exposes district grid axes as row/column. Public/user-facing
    // coordinates are X:Y = column:row, so canonical map storage must swap them.
    return {area_id:areaId, city_id:cityId, city_name:cityLabel(city), x:full?.info?.y ?? full?.meta?.gamearea_coords?.y,
      y:full?.info?.x ?? full?.meta?.gamearea_coords?.x, invest_count:Number(full?.info?.invest_count || invest.size),"""
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('mapAreaPayload coordinate anchor missing')

require(f"HK_MAP_COORDS_REV = '{REV}'","coordinate revision marker missing")
require("x:full?.info?.y ?? full?.meta?.gamearea_coords?.y","canonical X column mapping missing")
require("y:full?.info?.x ?? full?.meta?.gamearea_coords?.x","canonical Y row mapping missing")
require("Number(row?.x) === wantedY && Number(row?.y) === wantedX","Rumor raw-grid compatibility lost")
require("HK_MAP_SCANNER_REV = 'maps-building-scan-20260920-r2'","scanner r2 invariant lost")
require("HK_BUILDINGS_CANON_REV = 'buildings-canon-core-20260920-r1'","Buildings r1 invariant lost")
require("HK_STAGE2J_BOSSES_REV = 'bosses-area-target-20260920-r2'","Bosses invariant lost")
require("HK_PITS_REWARD_PICKER_REV = 'pits-reward-picker-20260920-r20'","Pits invariant lost")

TARGET.write_text(s,encoding='utf-8')
