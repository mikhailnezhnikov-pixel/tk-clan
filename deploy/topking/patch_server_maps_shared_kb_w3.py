from pathlib import Path

TARGET = Path("/tmp/server.py")
s = TARGET.read_text(encoding="utf-8")

def require(needle: str, message: str) -> None:
    if needle not in s:
        raise SystemExit(message)

anchor = '''def hk_map_area_link(map_key: str) -> dict | None:
    key = str(map_key or "").strip()
    with db_session() as db:
        row = db.execute(
            "SELECT map_key,canonical_area_id,match_method,linked_at FROM hk_map_area_links WHERE map_key=?",
            (key,),
        ).fetchone()
    return dict(row) if row else None


'''

insert = anchor + '''# HK_MAP_ROOM_KNOWLEDGE_W3_V1
def import_hk_map_room_knowledge(map_key: str, value: object) -> dict:
    """Fill only previously unknown canonical room counts for one linked website map.

    W3 intentionally does not overwrite any existing non-NULL room_count.
    Source priority/provenance normalization is handled in W5.
    """
    key = str(map_key or "").strip()
    if not re.fullmatch(r"hk_[a-z0-9]+", key):
        raise ValueError("invalid map key")
    if not isinstance(value, list) or len(value) > 5000:
        raise ValueError("invalid room knowledge")
    normalized = []
    seen = set()
    for raw in value:
        if not isinstance(raw, dict):
            continue
        building_id = str(raw.get("building_id", "")).strip()
        if not ID_RE.fullmatch(building_id) or building_id in seen:
            continue
        try:
            room_count = int(raw.get("room_count"))
        except (TypeError, ValueError):
            continue
        if not 0 <= room_count <= 20:
            continue
        seen.add(building_id)
        normalized.append({"building_id": building_id, "room_count": room_count})
    if not normalized:
        raise ValueError("no valid room knowledge")

    now = utc_now()
    source = "source-hk-maps-import"
    filled = preserved = missing = 0
    filled_ids = []
    preserved_ids = []
    missing_ids = []
    with db_session() as db:
        link = db.execute(
            "SELECT canonical_area_id FROM hk_map_area_links WHERE map_key=?",
            (key,),
        ).fetchone()
        if not link:
            raise LookupError("map is not linked to canonical area")
        area_id = str(link["canonical_area_id"])
        if not db.execute("SELECT 1 FROM map_areas WHERE area_id=?", (area_id,)).fetchone():
            raise LookupError("canonical area not found")

        for item in normalized:
            row = db.execute(
                """SELECT room_count FROM map_buildings
                   WHERE area_id=? AND building_id=?""",
                (area_id, item["building_id"]),
            ).fetchone()
            if not row:
                missing += 1
                missing_ids.append(item["building_id"])
                continue
            if row["room_count"] is not None:
                preserved += 1
                preserved_ids.append(item["building_id"])
                continue
            cursor = db.execute(
                """UPDATE map_buildings
                   SET room_count=?,
                       has_events=MAX(has_events,?),
                       last_player_id=?,
                       last_seen=?
                   WHERE area_id=? AND building_id=? AND room_count IS NULL""",
                (item["room_count"], int(item["room_count"] > 0), source, now,
                 area_id, item["building_id"]),
            )
            if cursor.rowcount:
                filled += 1
                filled_ids.append(item["building_id"])

        known, total, progress = map_completion(db, area_id)

    return {
        "ok": True,
        "map_key": key,
        "area_id": area_id,
        "requested": len(normalized),
        "filled": filled,
        "preserved_nonnull": preserved,
        "missing_buildings": missing,
        "filled_ids": filled_ids,
        "preserved_ids": preserved_ids,
        "missing_ids": missing_ids,
        "known_buildings": known,
        "buildings": total,
        "progress": progress,
        "source": source,
    }


'''
require(anchor, "W2 hk_map_area_link anchor missing")
s = s.replace(anchor, insert, 1)

cli_anchor = '''    elif "--link-hk-map-area" in os.sys.argv:
        if len(os.sys.argv) < 3:
            raise SystemExit("usage: server.py --link-hk-map-area MAP_KEY [AREA_ID]")
        init_db()
        print(json.dumps(link_hk_map_area(os.sys.argv[2], os.sys.argv[3] if len(os.sys.argv) > 3 else "")))
'''
cli_insert = cli_anchor + '''    elif "--import-hk-map-room-knowledge" in os.sys.argv:
        if len(os.sys.argv) < 4:
            raise SystemExit("usage: server.py --import-hk-map-room-knowledge MAP_KEY FILE.json")
        init_db()
        with open(os.sys.argv[3], "r", encoding="utf-8") as source:
            print(json.dumps(import_hk_map_room_knowledge(os.sys.argv[2], json.load(source))))
'''
require(cli_anchor, "W2 CLI anchor missing")
s = s.replace(cli_anchor, cli_insert, 1)

for marker in (
    "HK_MAP_AREA_LINKS_W2_V1",
    "HK_MAP_ROOM_KNOWLEDGE_W3_V1",
    "room_count IS NULL",
    'source = "source-hk-maps-import"',
    'elif "--import-hk-map-room-knowledge" in os.sys.argv:',
):
    require(marker, f"missing marker after W3 patch: {marker}")

TARGET.write_text(s, encoding="utf-8")
