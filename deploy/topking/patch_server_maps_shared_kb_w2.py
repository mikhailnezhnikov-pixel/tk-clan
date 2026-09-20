from pathlib import Path

TARGET = Path("/tmp/server.py")
s = TARGET.read_text(encoding="utf-8")

def require(needle: str, message: str) -> None:
    if needle not in s:
        raise SystemExit(message)

schema_anchor = '''            CREATE TABLE IF NOT EXISTS hk_map_points (
                map_key TEXT PRIMARY KEY,
                points_json TEXT NOT NULL DEFAULT '[]',
                point_count INTEGER NOT NULL DEFAULT 0,
                updated_at INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (map_key) REFERENCES hk_maps_catalog(map_key) ON DELETE CASCADE
            );
'''
schema_new = schema_anchor + '''            CREATE TABLE IF NOT EXISTS hk_map_area_links (
                map_key TEXT PRIMARY KEY,
                canonical_area_id TEXT NOT NULL,
                match_method TEXT NOT NULL CHECK(match_method IN ('exact_area_id','city_grid_yx')),
                linked_at INTEGER NOT NULL,
                FOREIGN KEY (map_key) REFERENCES hk_maps_catalog(map_key) ON DELETE CASCADE,
                FOREIGN KEY (canonical_area_id) REFERENCES map_areas(area_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_hk_map_area_links_canonical_area
                ON hk_map_area_links(canonical_area_id);
'''
require(schema_anchor, "hk_map_points schema anchor missing")
s = s.replace(schema_anchor, schema_new, 1)

helper_anchor = '''def hk_map_row(row: sqlite3.Row) -> dict:
    return {
        "key": row["map_key"], "city": row["city"], "grid": row["grid"],
        "invest": row["invest"], "buildings": row["buildings"], "unknown": row["unknown"],
        "crystals": [row[f"c{i}"] for i in range(6)],
        "eventBuildings": row["event_buildings"], "totalEvents": row["total_events"],
        "progress": row["progress"], "score": row["score"],
        "reward": {"max": row["reward_max"], "normal": row["reward_normal"],
                   "investment": row["reward_investment"]},
        "open_url": row["open_url"], "published": bool(row["published"]),
    }


'''
helpers = helper_anchor + '''# HK_MAP_AREA_LINKS_W2_V1
def _canonical_area_id(db: sqlite3.Connection, area_id: str) -> str | None:
    value = str(area_id or "").strip()
    if not value:
        return None
    alias = db.execute(
        "SELECT canonical_area_id FROM map_area_aliases WHERE source_area_id=?",
        (value,),
    ).fetchone()
    canonical = str(alias["canonical_area_id"]) if alias else value
    exists = db.execute("SELECT 1 FROM map_areas WHERE area_id=?", (canonical,)).fetchone()
    return canonical if exists else None


def discover_hk_map_area(db: sqlite3.Connection, map_key: str) -> dict:
    key = str(map_key or "").strip()
    if not re.fullmatch(r"hk_[a-z0-9]+", key):
        raise ValueError("invalid map key")
    row = db.execute("SELECT map_key,city,grid FROM hk_maps_catalog WHERE map_key=?", (key,)).fetchone()
    if not row:
        raise LookupError("map not found")
    match = re.fullmatch(r"\\s*(\\d{1,3})\\s*:\\s*(\\d{1,3})\\s*", str(row["grid"] or ""))
    if not match:
        return {"map_key": key, "city": row["city"], "grid": row["grid"],
                "match_method": "city_grid_yx", "candidates": []}
    # Historical HK Maps labels grid as Y:X. Canonical TopKing stores X:Y.
    y, x = int(match.group(1)), int(match.group(2))
    city_key = map_city_key(row["city"])
    candidates: set[str] = set()
    for area in db.execute(
        "SELECT area_id,city_id,city_name FROM map_areas WHERE x=? AND y=?",
        (x, y),
    ).fetchall():
        area_city_keys = {map_city_key(area["city_name"]), map_city_key(area["city_id"])}
        if city_key not in area_city_keys:
            continue
        canonical = _canonical_area_id(db, str(area["area_id"]))
        if canonical:
            candidates.add(canonical)
    return {"map_key": key, "city": row["city"], "grid": row["grid"],
            "x": x, "y": y, "match_method": "city_grid_yx",
            "candidates": sorted(candidates)}


def link_hk_map_area(map_key: str, area_id: str = "") -> dict:
    key = str(map_key or "").strip()
    with db_session() as db:
        map_row = db.execute("SELECT 1 FROM hk_maps_catalog WHERE map_key=?", (key,)).fetchone()
        if not map_row:
            raise LookupError("map not found")
        requested = str(area_id or "").strip()
        if requested:
            canonical = _canonical_area_id(db, requested)
            if not canonical:
                raise LookupError("canonical area not found")
            method = "exact_area_id"
            candidates = [canonical]
        else:
            discovered = discover_hk_map_area(db, key)
            candidates = discovered["candidates"]
            method = discovered["match_method"]
            if len(candidates) != 1:
                raise ValueError(f"map link requires exactly one canonical candidate, got {len(candidates)}")
            canonical = candidates[0]
        now = utc_now()
        db.execute(
            """INSERT INTO hk_map_area_links(map_key,canonical_area_id,match_method,linked_at)
               VALUES(?,?,?,?)
               ON CONFLICT(map_key) DO UPDATE SET
               canonical_area_id=excluded.canonical_area_id,
               match_method=excluded.match_method,
               linked_at=excluded.linked_at""",
            (key, canonical, method, now),
        )
        linked = db.execute(
            "SELECT map_key,canonical_area_id,match_method,linked_at FROM hk_map_area_links WHERE map_key=?",
            (key,),
        ).fetchone()
    return {"ok": True, "link": dict(linked), "candidates": candidates}


def hk_map_area_link(map_key: str) -> dict | None:
    key = str(map_key or "").strip()
    with db_session() as db:
        row = db.execute(
            "SELECT map_key,canonical_area_id,match_method,linked_at FROM hk_map_area_links WHERE map_key=?",
            (key,),
        ).fetchone()
    return dict(row) if row else None


'''
require(helper_anchor, "hk_map_row helper anchor missing")
s = s.replace(helper_anchor, helpers, 1)

cli_anchor = '''    elif "--import-kokkaras-map" in os.sys.argv:
        if len(os.sys.argv) < 3:
            raise SystemExit("usage: server.py --import-kokkaras-map FILE.json.gz")
        init_db()
        with gzip.open(os.sys.argv[2], "rt", encoding="utf-8") as source:
            print(json.dumps(import_kokkaras_map(json.load(source))))
'''
cli_new = '''    elif "--link-hk-map-area" in os.sys.argv:
        if len(os.sys.argv) < 3:
            raise SystemExit("usage: server.py --link-hk-map-area MAP_KEY [AREA_ID]")
        init_db()
        print(json.dumps(link_hk_map_area(os.sys.argv[2], os.sys.argv[3] if len(os.sys.argv) > 3 else "")))
''' + cli_anchor
require(cli_anchor, "CLI anchor missing")
s = s.replace(cli_anchor, cli_new, 1)

for marker in (
    "CREATE TABLE IF NOT EXISTS hk_map_area_links",
    "HK_MAP_AREA_LINKS_W2_V1",
    "Historical HK Maps labels grid as Y:X",
    'elif "--link-hk-map-area" in os.sys.argv:',
):
    require(marker, f"missing marker after patch: {marker}")

TARGET.write_text(s, encoding="utf-8")
