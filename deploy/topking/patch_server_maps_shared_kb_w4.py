from pathlib import Path

TARGET=Path("/tmp/server.py")
s=TARGET.read_text(encoding="utf-8")

def require(x,msg):
    if x not in s:
        raise SystemExit(msg)

schema_anchor='''            CREATE INDEX IF NOT EXISTS idx_hk_map_area_links_canonical_area
                ON hk_map_area_links(canonical_area_id);
'''
schema_new=schema_anchor+'''            CREATE TABLE IF NOT EXISTS hk_map_point_links (
                map_key TEXT NOT NULL,
                point_index INTEGER NOT NULL CHECK(point_index >= 0),
                building_id TEXT NOT NULL,
                match_method TEXT NOT NULL CHECK(match_method IN ('osm_point_in_polygon','exact_building_id')),
                linked_at INTEGER NOT NULL,
                PRIMARY KEY(map_key,point_index),
                FOREIGN KEY (map_key) REFERENCES hk_maps_catalog(map_key) ON DELETE CASCADE
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_hk_map_point_links_building
                ON hk_map_point_links(map_key,building_id);
'''
require(schema_anchor,"W2 point-link schema anchor missing")
s=s.replace(schema_anchor,schema_new,1)

helper_anchor='''# HK_MAP_ROOM_KNOWLEDGE_W3_V1
'''
helpers='''# HK_MAP_WEBSITE_OVERLAY_W4_V1
def link_hk_map_points(map_key: str, value: object, match_method: str = "osm_point_in_polygon") -> dict:
    key = str(map_key or "").strip()
    if not re.fullmatch(r"hk_[a-z0-9]+", key):
        raise ValueError("invalid map key")
    if match_method not in {"osm_point_in_polygon", "exact_building_id"}:
        raise ValueError("invalid point link method")
    if not isinstance(value, list) or len(value) > 5000:
        raise ValueError("invalid point links")
    now = utc_now()
    with db_session() as db:
        bridge = db.execute(
            "SELECT canonical_area_id FROM hk_map_area_links WHERE map_key=?",
            (key,),
        ).fetchone()
        if not bridge:
            raise LookupError("map is not linked to canonical area")
        area_id = str(bridge["canonical_area_id"])
        point_row = db.execute(
            "SELECT point_count FROM hk_map_points WHERE map_key=?",
            (key,),
        ).fetchone()
        if not point_row:
            raise LookupError("map points not found")
        point_count = int(point_row["point_count"])
        normalized = []
        seen_points = set()
        seen_buildings = set()
        for raw in value:
            if not isinstance(raw, dict):
                continue
            try:
                point_index = int(raw.get("point_index"))
            except (TypeError, ValueError):
                continue
            building_id = str(raw.get("building_id") or "").strip()
            if not 0 <= point_index < point_count:
                continue
            if not ID_RE.fullmatch(building_id):
                continue
            if point_index in seen_points or building_id in seen_buildings:
                continue
            exists = db.execute(
                "SELECT 1 FROM map_buildings WHERE area_id=? AND building_id=?",
                (area_id, building_id),
            ).fetchone()
            if not exists:
                continue
            seen_points.add(point_index)
            seen_buildings.add(building_id)
            normalized.append((point_index, building_id))
        if not normalized:
            raise ValueError("no valid point links")
        for point_index, building_id in normalized:
            db.execute(
                """INSERT INTO hk_map_point_links(map_key,point_index,building_id,match_method,linked_at)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(map_key,point_index) DO UPDATE SET
                     building_id=excluded.building_id,
                     match_method=excluded.match_method,
                     linked_at=excluded.linked_at""",
                (key, point_index, building_id, match_method, now),
            )
        total = db.execute(
            "SELECT COUNT(*) FROM hk_map_point_links WHERE map_key=?",
            (key,),
        ).fetchone()[0]
    return {"ok": True, "map_key": key, "area_id": area_id,
            "linked": len(normalized), "total": int(total), "match_method": match_method}


def hk_map_points_with_canonical(map_key: str, flat: object) -> tuple[list, dict]:
    points = list(flat) if isinstance(flat, list) else []
    point_count = len(points) // 3
    meta = {"enabled": False, "linked_points": 0, "applied_points": 0,
            "fallback_points": point_count, "canonical_area_id": ""}
    if not points or len(points) % 3:
        return points, meta
    with db_session() as db:
        bridge = db.execute(
            "SELECT canonical_area_id FROM hk_map_area_links WHERE map_key=?",
            (map_key,),
        ).fetchone()
        if not bridge:
            return points, meta
        area_id = str(bridge["canonical_area_id"])
        rows = db.execute(
            """SELECT p.point_index,p.building_id,b.room_count
               FROM hk_map_point_links p
               LEFT JOIN map_buildings b
                 ON b.area_id=? AND b.building_id=p.building_id
               WHERE p.map_key=? ORDER BY p.point_index""",
            (area_id, map_key),
        ).fetchall()
    meta["enabled"] = bool(rows)
    meta["canonical_area_id"] = area_id
    meta["linked_points"] = len(rows)
    applied = 0
    for row in rows:
        point_index = int(row["point_index"])
        slot = point_index * 3 + 2
        if not 0 <= slot < len(points):
            continue
        room_count = row["room_count"]
        if room_count is None:
            continue
        try:
            rooms = int(room_count)
            old_flag = int(points[slot])
        except (TypeError, ValueError):
            continue
        if not 0 <= rooms <= 5:
            continue
        investment = old_flag >= 7
        points[slot] = rooms + 8 if investment else rooms
        applied += 1
    meta["applied_points"] = applied
    meta["fallback_points"] = max(0, point_count - applied)
    return points, meta


''' + helper_anchor
require(helper_anchor,"W3 helper anchor missing")
s=s.replace(helper_anchor,helpers,1)

old='''    try:
        points = json.loads(row["points_json"])
    except json.JSONDecodeError:
        points = []
    return {"ok": True, "map": hk_map_row(row), "point_count": row["point_count"],
            "render": "points", "points": points}
'''
new='''    try:
        points = json.loads(row["points_json"])
    except json.JSONDecodeError:
        points = []
    points, canonical = hk_map_points_with_canonical(map_key, points)
    return {"ok": True, "map": hk_map_row(row), "point_count": row["point_count"],
            "render": "points", "points": points, "canonical": canonical}
'''
require(old,"hk_map_data points return anchor missing")
s=s.replace(old,new,1)

cli_anchor='''    elif "--import-hk-map-room-knowledge" in os.sys.argv:
        if len(os.sys.argv) < 4:
            raise SystemExit("usage: server.py --import-hk-map-room-knowledge MAP_KEY FILE.json")
        init_db()
        with open(os.sys.argv[3], "r", encoding="utf-8") as source:
            print(json.dumps(import_hk_map_room_knowledge(os.sys.argv[2], json.load(source))))
'''
cli_new=cli_anchor+'''    elif "--link-hk-map-points" in os.sys.argv:
        if len(os.sys.argv) < 4:
            raise SystemExit("usage: server.py --link-hk-map-points MAP_KEY FILE.json")
        init_db()
        with open(os.sys.argv[3], "r", encoding="utf-8") as source:
            print(json.dumps(link_hk_map_points(os.sys.argv[2], json.load(source))))
'''
require(cli_anchor,"W3 CLI anchor missing")
s=s.replace(cli_anchor,cli_new,1)

for marker in (
    "HK_MAP_WEBSITE_OVERLAY_W4_V1",
    "CREATE TABLE IF NOT EXISTS hk_map_point_links",
    "def hk_map_points_with_canonical",
    'elif "--link-hk-map-points" in os.sys.argv:',
    '"canonical": canonical',
):
    require(marker,"missing W4 marker: "+marker)

TARGET.write_text(s,encoding="utf-8")
