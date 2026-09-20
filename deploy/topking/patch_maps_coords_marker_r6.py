from pathlib import Path
TARGET=Path('/tmp/HamsterKingMobile.user.js')
s=TARGET.read_text(encoding='utf-8')

def require(n,m):
    if n not in s: raise SystemExit(m)

require("HK_MAP_SCANNER_REV = 'maps-parallel-read-20260920-r5'","scanner r5 missing")
require("HK_MAP_COORDS_REV = 'maps-coordinates-column-row-20260920-r1'","coords r1 missing")
old="""    return {area_id:areaId, city_id:cityId, city_name:cityLabel(city), x:full?.info?.y ?? full?.meta?.gamearea_coords?.y,
      y:full?.info?.x ?? full?.meta?.gamearea_coords?.x, invest_count:Number(full?.info?.invest_count || invest.size),"""
new="""    return {area_id:areaId, city_id:cityId, city_name:cityLabel(city), coord_revision:'column-row-v1',
      x:full?.info?.y ?? full?.meta?.gamearea_coords?.y,
      y:full?.info?.x ?? full?.meta?.gamearea_coords?.x, invest_count:Number(full?.info?.invest_count || invest.size),"""
require(old,"mapAreaPayload coords anchor missing")
s=s.replace(old,new,1)
s=s.replace("HK_MAP_COORDS_REV = 'maps-coordinates-column-row-20260920-r1'",
            "HK_MAP_COORDS_REV = 'maps-coordinates-column-row-20260920-r2'",1)

require("coord_revision:'column-row-v1'","coord revision payload missing")
require("HK_MAP_COORDS_REV = 'maps-coordinates-column-row-20260920-r2'","coords r2 marker missing")
require("HK_MAP_SCANNER_REV = 'maps-parallel-read-20260920-r5'","scanner r5 invariant lost")
require("const HK_MAP_READ_CONCURRENCY = 10;","parallel read invariant lost")
require("const HK_MAP_SUBMIT_BATCH = 200;","batch invariant lost")
require("HK_BUILDINGS_CANON_REV = 'buildings-canon-core-20260920-r1'","buildings invariant lost")
TARGET.write_text(s,encoding='utf-8')
