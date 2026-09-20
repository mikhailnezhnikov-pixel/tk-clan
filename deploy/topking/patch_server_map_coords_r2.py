from pathlib import Path
TARGET=Path('/tmp/server.py')
s=TARGET.read_text(encoding='utf-8')

def require(n,m):
    if n not in s: raise SystemExit(m)

old_return='''    return {"area_id":area_id, "city_id":city_id, "city_name":str(value.get("city_name", ""))[:120],
            "x":None if value.get("x") is None else int(value.get("x")), "y":None if value.get("y") is None else int(value.get("y")),
            "invest_count":max(0,int(value.get("invest_count") or 0)), "expected_buildings":max(0,int(value.get("expected_buildings") or len(normalized))),
            "buildings":normalized}
'''
new_return='''    return {"area_id":area_id, "city_id":city_id, "city_name":str(value.get("city_name", ""))[:120],
            "coord_revision":str(value.get("coord_revision", ""))[:64],
            "x":None if value.get("x") is None else int(value.get("x")), "y":None if value.get("y") is None else int(value.get("y")),
            "invest_count":max(0,int(value.get("invest_count") or 0)), "expected_buildings":max(0,int(value.get("expected_buildings") or len(normalized))),
            "buildings":normalized}
'''
require(old_return,"normalize_map_area return anchor missing")
s=s.replace(old_return,new_return,1)

old_existing='''        existing = db.execute("SELECT 1 FROM map_areas WHERE area_id=?", (canonical_id,)).fetchone()
        if existing:
            known, total, progress = map_completion(db, canonical_id)
'''
new_existing='''        existing = db.execute("SELECT 1 FROM map_areas WHERE area_id=?", (canonical_id,)).fetchone()
        trusted_coords = area.get("coord_revision") == "column-row-v1"
        if existing:
            # Coordinates in older rows were stored in raw API row:column order.
            # Only the explicitly versioned column:row payload may replace them.
            # Do this before the completed-map early return.
            if trusted_coords and area["x"] is not None and area["y"] is not None:
                db.execute("""UPDATE map_areas
                              SET x=?,y=?,last_player_id=?,last_seen=?
                              WHERE area_id=?""",
                           (area["x"],area["y"],player_id,now,canonical_id))
            known, total, progress = map_completion(db, canonical_id)
'''
require(old_existing,"submit_map_area existing anchor missing")
s=s.replace(old_existing,new_existing,1)

require('"coord_revision":str(value.get("coord_revision", ""))[:64]',"coord revision normalization missing")
require('trusted_coords = area.get("coord_revision") == "column-row-v1"',"trusted coord gate missing")
require('SET x=?,y=?,last_player_id=?,last_seen=?',"coordinate update missing")
require('if total and known >= total:',"complete-map guard lost")
require('x=COALESCE(map_areas.x,excluded.x),y=COALESCE(map_areas.y,excluded.y)',"legacy unversioned coordinate protection lost")
TARGET.write_text(s,encoding='utf-8')
