from pathlib import Path
import json

TARGET=Path("/tmp/server.py")
s=TARGET.read_text(encoding="utf-8")

def req(value,message):
    if value not in s:
        raise SystemExit(message)

MARKER="# HK_MAP_GAME_GEOMETRY_R1\n"
if MARKER in s:
    print("HK_MAP_GAME_GEOMETRY_R1_ALREADY_PRESENT")
    raise SystemExit(0)

req("def hk_map_data(map_key: str, member: dict | None = None, public: bool = False) -> dict:\n","hk_map_data missing")
req("def submit_map_area(player_id: str, value: object) -> dict:\n","submit_map_area missing")
req("full = load_full_hk_map(map_key)","full map fallback anchor missing")
req("area, now = normalize_map_area(value), utc_now()","submit start anchor missing")
req("canonical_id = overlap_canonical or canonical_map_area(db, area)","canonical id anchor missing")

helpers=r'''# HK_MAP_GAME_GEOMETRY_R1
# Persist the exact game building geometry received from /game_area/{id}.
# Website map rendering then uses these real game contours instead of OSM
# points or synthetic rectangles.
def _hk_game_geometry_collection(value: object) -> dict | None:
    if isinstance(value, str):
        try:
            value=json.loads(value)
        except Exception:
            return None
    if isinstance(value, list):
        features=value
    elif isinstance(value, dict) and isinstance(value.get("features"), list):
        features=value["features"]
    else:
        return None
    if not features or len(features)>12000:
        return None

    clean=[]
    for raw in features:
        if not isinstance(raw, dict):
            continue
        geometry=raw.get("geometry")
        if not isinstance(geometry, dict):
            continue
        kind=str(geometry.get("type") or "")
        if kind not in ("Polygon","MultiPolygon","Point"):
            continue
        coords=geometry.get("coordinates")
        if not isinstance(coords, list):
            continue
        props=raw.get("properties") if isinstance(raw.get("properties"),dict) else {}
        kept={}
        for key in ("building_id","buildingId","id","is_game","is_investment","color","base_color","faction","building_generator","building_type"):
            if key in props:
                kept[key]=props[key]
        feature={"type":"Feature","geometry":{"type":kind,"coordinates":coords},"properties":kept}
        if raw.get("id") is not None:
            feature["id"]=raw.get("id")
        clean.append(feature)
    if not clean:
        return None
    result={"type":"FeatureCollection","features":clean}
    raw=json.dumps(result,separators=(",",":"),ensure_ascii=False)
    if len(raw.encode("utf-8"))>20*1024*1024:
        return None
    return result


def _hk_ensure_game_geometry_schema(db: sqlite3.Connection) -> None:
    db.execute("""CREATE TABLE IF NOT EXISTS hk_map_area_geometry(
        canonical_area_id TEXT PRIMARY KEY,
        geometry_json TEXT NOT NULL,
        feature_count INTEGER NOT NULL DEFAULT 0,
        observed_at INTEGER NOT NULL DEFAULT 0,
        source TEXT NOT NULL DEFAULT 'game_live'
    )""")


def _hk_store_game_geometry(db: sqlite3.Connection, area_id: str, value: object, observed_at: int) -> int:
    collection=_hk_game_geometry_collection(value)
    if not collection:
        return 0
    _hk_ensure_game_geometry_schema(db)
    raw=json.dumps(collection,separators=(",",":"),ensure_ascii=False)
    count=len(collection["features"])
    db.execute("""INSERT INTO hk_map_area_geometry(canonical_area_id,geometry_json,feature_count,observed_at,source)
                  VALUES(?,?,?,?,?)
                  ON CONFLICT(canonical_area_id) DO UPDATE SET
                    geometry_json=excluded.geometry_json,
                    feature_count=excluded.feature_count,
                    observed_at=excluded.observed_at,
                    source=excluded.source""",
               (str(area_id),raw,count,int(observed_at),"game_live"))
    return count


def _hk_feature_building_id(feature: dict) -> str:
    props=feature.get("properties") if isinstance(feature.get("properties"),dict) else {}
    return str(props.get("building_id") or props.get("buildingId") or feature.get("id") or props.get("id") or "").strip()


def _hk_geometry_pairs(value: object, output: list | None = None) -> list:
    if output is None:
        output=[]
    if isinstance(value,(list,tuple)):
        if len(value)>=2 and isinstance(value[0],(int,float)) and isinstance(value[1],(int,float)):
            output.append((float(value[0]),float(value[1])))
        else:
            for child in value:
                _hk_geometry_pairs(child,output)
    return output


def load_live_game_geometry_hk_map(map_key: str) -> dict | None:
    with db_session() as db:
        link=db.execute("SELECT canonical_area_id FROM hk_map_area_links WHERE map_key=?",(map_key,)).fetchone()
        if not link:
            return None
        area_id=str(link["canonical_area_id"])
        _hk_ensure_game_geometry_schema(db)
        stored=db.execute("""SELECT geometry_json,feature_count,observed_at
                             FROM hk_map_area_geometry WHERE canonical_area_id=?""",(area_id,)).fetchone()
        if not stored:
            return None
        try:
            collection=json.loads(stored["geometry_json"])
        except Exception:
            return None
        rows=db.execute("""SELECT building_id,room_count,is_invest,faction,building_type
                           FROM map_buildings WHERE area_id=?""",(area_id,)).fetchall()
        known={str(row["building_id"]):dict(row) for row in rows}
        catalog=db.execute("SELECT city,grid FROM hk_maps_catalog WHERE map_key=?",(map_key,)).fetchone()

    palette={
        "NULL":"#62656b","0":"#72494a","1":"#807140","2":"#895d3e",
        "3":"#65446d","4":"#406d54","5":"#416978","6":"#426c68","7":"#707174"
    }
    features=[]
    all_pairs=[]
    for raw in collection.get("features") or []:
        if not isinstance(raw,dict) or not isinstance(raw.get("geometry"),dict):
            continue
        feature={"type":"Feature","geometry":raw["geometry"],"properties":dict(raw.get("properties") or {})}
        if raw.get("id") is not None:
            feature["id"]=raw.get("id")
        bid=_hk_feature_building_id(raw)
        row=known.get(bid)
        props=feature["properties"]
        is_game=bool(row) or bool(props.get("is_game"))
        props["is_game"]=is_game
        if bid:
            props["building_id"]=bid
        if row:
            room=row.get("room_count")
            key="NULL" if room is None else str(max(0,min(7,int(room))))
            props["crystals_key"]=key
            props["crystals"]=None if room is None else int(room)
            props["is_investment"]=bool(row.get("is_invest"))
            if row.get("faction"):
                props["faction"]=row.get("faction")
            if row.get("building_type"):
                props["building_generator"]=row.get("building_type")
            props["base_color"]=palette.get(key,"#62656b")
        else:
            props["crystals_key"]="NULL"
            props["base_color"]=str(props.get("base_color") or props.get("color") or "#4b4b50")
        all_pairs.extend(_hk_geometry_pairs(feature["geometry"].get("coordinates")))
        features.append(feature)

    if not features or not all_pairs:
        return None
    xs=[p[0] for p in all_pairs]; ys=[p[1] for p in all_pairs]
    bounds=[[min(xs),min(ys)],[max(xs),max(ys)]]
    center=[(bounds[0][0]+bounds[1][0])/2,(bounds[0][1]+bounds[1][1])/2]
    empty={"type":"FeatureCollection","features":[]}
    title=" ".join([str(catalog["city"] or "") if catalog else "",str(catalog["grid"] or "") if catalog else ""]).strip()
    return {
        "title":title or map_key,
        "source":"game_live_geometry",
        "observed_at":int(stored["observed_at"] or 0),
        "bounds":bounds,
        "center":center,
        "landuse":empty,
        "water":empty,
        "roads":empty,
        "buildings":{"type":"FeatureCollection","features":features},
    }


'''
s=s.replace("def hk_map_data(map_key: str, member: dict | None = None, public: bool = False) -> dict:\n",
            helpers+"def hk_map_data(map_key: str, member: dict | None = None, public: bool = False) -> dict:\n",1)

s=s.replace("    full = load_full_hk_map(map_key)\n    if full is not None:\n",
            "    full = load_full_hk_map(map_key)\n    if full is None:\n        full = load_live_game_geometry_hk_map(map_key)\n    if full is not None:\n",1)

s=s.replace("def submit_map_area(player_id: str, value: object) -> dict:\n    area, now = normalize_map_area(value), utc_now()\n",
            "def submit_map_area(player_id: str, value: object) -> dict:\n    raw_game_geometry = value.get('_website_geometry') if isinstance(value,dict) else None\n    area, now = normalize_map_area(value), utc_now()\n",1)

s=s.replace("        canonical_id = overlap_canonical or canonical_map_area(db, area)\n",
            "        canonical_id = overlap_canonical or canonical_map_area(db, area)\n        if knowledge_source == 'game_live' and raw_game_geometry is not None:\n            _hk_store_game_geometry(db,canonical_id,raw_game_geometry,now)\n",1)

for marker in (
    "HK_MAP_GAME_GEOMETRY_R1",
    "def load_live_game_geometry_hk_map",
    "CREATE TABLE IF NOT EXISTS hk_map_area_geometry",
    "full = load_live_game_geometry_hk_map(map_key)",
    "_hk_store_game_geometry(db,canonical_id,raw_game_geometry,now)",
):
    req(marker,"missing game geometry marker: "+marker)

TARGET.write_text(s,encoding="utf-8")
print("HK_MAP_GAME_GEOMETRY_R1_PATCH=PASS")
