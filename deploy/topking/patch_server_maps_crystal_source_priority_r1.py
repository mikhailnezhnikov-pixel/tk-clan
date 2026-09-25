from pathlib import Path
import re, sys

TARGET=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/server.py")
s=TARGET.read_text(encoding="utf-8")

def req(old,label,count=1):
    actual=s.count(old)
    if actual!=count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")

def repl(old,new,label,count=1):
    global s
    req(old,label,count)
    s=s.replace(old,new,count)

MARKER="# HK_MAP_CRYSTAL_SOURCE_PRIORITY_R1\n"
if MARKER in s:
    print("HK_MAP_CRYSTAL_SOURCE_PRIORITY_R1_ALREADY_PRESENT")
    raise SystemExit(0)

anchor="# HK_MAP_PROVENANCE_W5_V1\n"
req(anchor,"W5 provenance anchor")
schema=r'''# HK_MAP_CRYSTAL_SOURCE_PRIORITY_R1
def ensure_hk_map_source_crystals_schema(db: sqlite3.Connection) -> None:
    db.execute("""CREATE TABLE IF NOT EXISTS hk_map_source_crystals(
        map_key TEXT NOT NULL,
        canonical_area_id TEXT NOT NULL,
        building_id TEXT NOT NULL,
        room_count INTEGER,
        is_invest INTEGER NOT NULL DEFAULT 0,
        observed_at INTEGER NOT NULL DEFAULT 0,
        source TEXT NOT NULL DEFAULT 'full235_archive',
        PRIMARY KEY(map_key,building_id)
    )""")
    db.execute("""CREATE INDEX IF NOT EXISTS idx_hk_map_source_crystals_area_building
                  ON hk_map_source_crystals(canonical_area_id,building_id)""")


def hk_source_crystal_row(db: sqlite3.Connection, area_id: str, building_id: str) -> sqlite3.Row | None:
    ensure_hk_map_source_crystals_schema(db)
    return db.execute("""SELECT room_count,is_invest,map_key,observed_at
                         FROM hk_map_source_crystals
                         WHERE canonical_area_id=? AND building_id=?
                         ORDER BY observed_at DESC LIMIT 1""",
                      (str(area_id),str(building_id))).fetchone()


''' + anchor
s=s.replace(anchor,schema,1)

# Imported source data must be allowed to refresh even a fully-known map.
repl(
    '            if total and known >= total and knowledge_source != "game_live":\n',
    '            if total and known >= total and knowledge_source not in ("game_live","hk_maps_import"):\n',
    "complete-map source refresh",
)

old_room="""                        room_count=CASE
                          WHEN excluded.room_count IS NULL THEN map_buildings.room_count
                          WHEN excluded.knowledge_source='game_live' THEN excluded.room_count
                          WHEN map_buildings.room_count IS NULL THEN excluded.room_count
                          ELSE map_buildings.room_count END,
                        has_events=CASE
                          WHEN excluded.room_count IS NOT NULL
                           AND (excluded.knowledge_source='game_live' OR map_buildings.room_count IS NULL)
                          THEN excluded.has_events
                          ELSE MAX(map_buildings.has_events,excluded.has_events) END,"""
new_room="""                        room_count=CASE
                          WHEN excluded.knowledge_source='hk_maps_import' THEN excluded.room_count
                          WHEN map_buildings.knowledge_source='hk_maps_import' THEN map_buildings.room_count
                          WHEN excluded.room_count IS NULL THEN map_buildings.room_count
                          WHEN excluded.knowledge_source='game_live' THEN excluded.room_count
                          WHEN map_buildings.room_count IS NULL THEN excluded.room_count
                          ELSE map_buildings.room_count END,
                        has_events=CASE
                          WHEN excluded.knowledge_source='hk_maps_import' THEN excluded.has_events
                          WHEN map_buildings.knowledge_source='hk_maps_import' THEN map_buildings.has_events
                          WHEN excluded.room_count IS NOT NULL
                           AND (excluded.knowledge_source='game_live' OR map_buildings.room_count IS NULL)
                          THEN excluded.has_events
                          ELSE MAX(map_buildings.has_events,excluded.has_events) END,"""
repl(old_room,new_room,"submit source-priority room SQL")

old_provenance="""                        last_player_id=CASE
                          WHEN excluded.room_count IS NOT NULL
                           AND (excluded.knowledge_source='game_live' OR map_buildings.room_count IS NULL)
                          THEN excluded.last_player_id ELSE map_buildings.last_player_id END,
                        last_seen=MAX(map_buildings.last_seen,excluded.last_seen),
                        knowledge_source=CASE
                          WHEN excluded.room_count IS NOT NULL
                           AND (excluded.knowledge_source='game_live' OR map_buildings.room_count IS NULL)
                          THEN excluded.knowledge_source ELSE map_buildings.knowledge_source END,
                        knowledge_observed_at=CASE
                          WHEN excluded.room_count IS NOT NULL
                           AND (excluded.knowledge_source='game_live' OR map_buildings.room_count IS NULL)
                          THEN excluded.knowledge_observed_at ELSE map_buildings.knowledge_observed_at END"""
new_provenance="""                        last_player_id=CASE
                          WHEN excluded.knowledge_source='hk_maps_import' THEN excluded.last_player_id
                          WHEN map_buildings.knowledge_source='hk_maps_import' THEN map_buildings.last_player_id
                          WHEN excluded.room_count IS NOT NULL
                           AND (excluded.knowledge_source='game_live' OR map_buildings.room_count IS NULL)
                          THEN excluded.last_player_id ELSE map_buildings.last_player_id END,
                        last_seen=MAX(map_buildings.last_seen,excluded.last_seen),
                        knowledge_source=CASE
                          WHEN excluded.knowledge_source='hk_maps_import' THEN 'hk_maps_import'
                          WHEN map_buildings.knowledge_source='hk_maps_import' THEN 'hk_maps_import'
                          WHEN excluded.room_count IS NOT NULL
                           AND (excluded.knowledge_source='game_live' OR map_buildings.room_count IS NULL)
                          THEN excluded.knowledge_source ELSE map_buildings.knowledge_source END,
                        knowledge_observed_at=CASE
                          WHEN excluded.knowledge_source='hk_maps_import' THEN excluded.knowledge_observed_at
                          WHEN map_buildings.knowledge_source='hk_maps_import' THEN map_buildings.knowledge_observed_at
                          WHEN excluded.room_count IS NOT NULL
                           AND (excluded.knowledge_source='game_live' OR map_buildings.room_count IS NULL)
                          THEN excluded.knowledge_observed_at ELSE map_buildings.knowledge_observed_at END"""
repl(old_provenance,new_provenance,"submit source-priority provenance SQL")

# Full235 archive rows are authoritative, including explicit unknown (NULL).
full_room="""        room_count=CASE
          WHEN excluded.room_count IS NULL THEN map_buildings.room_count
          WHEN map_buildings.knowledge_source='game_live' AND map_buildings.room_count IS NOT NULL THEN map_buildings.room_count
          ELSE excluded.room_count END,
        has_events=CASE
          WHEN excluded.room_count IS NULL THEN map_buildings.has_events
          WHEN map_buildings.knowledge_source='game_live' AND map_buildings.room_count IS NOT NULL THEN map_buildings.has_events
          ELSE excluded.has_events END,"""
repl(full_room,"""        room_count=excluded.room_count,
        has_events=excluded.has_events,""","Full235 room priority")

full_prov="""        last_player_id=CASE
          WHEN excluded.room_count IS NULL THEN map_buildings.last_player_id
          WHEN map_buildings.knowledge_source='game_live' AND map_buildings.room_count IS NOT NULL THEN map_buildings.last_player_id
          ELSE excluded.last_player_id END,
        last_seen=MAX(map_buildings.last_seen,excluded.last_seen),
        knowledge_source=CASE
          WHEN excluded.room_count IS NULL THEN map_buildings.knowledge_source
          WHEN map_buildings.knowledge_source='game_live' AND map_buildings.room_count IS NOT NULL THEN map_buildings.knowledge_source
          ELSE excluded.knowledge_source END,
        knowledge_observed_at=CASE
          WHEN excluded.room_count IS NULL THEN map_buildings.knowledge_observed_at
          WHEN map_buildings.knowledge_source='game_live' AND map_buildings.room_count IS NOT NULL THEN map_buildings.knowledge_observed_at
          ELSE excluded.knowledge_observed_at END"""
repl(full_prov,"""        last_player_id=excluded.last_player_id,
        last_seen=MAX(map_buildings.last_seen,excluded.last_seen),
        knowledge_source='hk_maps_import',
        knowledge_observed_at=excluded.knowledge_observed_at""","Full235 provenance priority")

# Compact uploaded map points are already the source truth. Never repaint their
# crystal bits from shared/live knowledge.
start=s.find("def hk_map_points_with_canonical(map_key: str, flat: object) -> tuple[list, dict]:")
end=s.find("\n\n# HK_MAP_ROOM_KNOWLEDGE_W3_V1",start)
if start<0 or end<0:
    raise SystemExit("hk_map_points_with_canonical block missing")
new_points=r'''def hk_map_points_with_canonical(map_key: str, flat: object) -> tuple[list, dict]:
    points = list(flat) if isinstance(flat, list) else []
    point_count = len(points) // 3
    meta = {"enabled": False, "linked_points": 0, "applied_points": 0,
            "fallback_points": point_count, "canonical_area_id": "",
            "crystal_source": "uploaded_map"}
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
        linked = db.execute(
            "SELECT COUNT(*) FROM hk_map_point_links WHERE map_key=?",
            (map_key,),
        ).fetchone()[0]
    meta["enabled"] = bool(linked)
    meta["canonical_area_id"] = area_id
    meta["linked_points"] = int(linked or 0)
    # Source crystal bits are immutable here. Canonical/live knowledge can
    # enrich other metadata, but never changes crystals on the uploaded map.
    return points, meta
'''
s=s[:start]+new_points+s[end:]

# Known room imports from the uploaded source overwrite live values.
old_preserve='''            if row["room_count"] is not None:
                preserved += 1
                preserved_ids.append(item["building_id"])
                continue
            cursor = db.execute(
                """UPDATE map_buildings
                   SET room_count=?,
                       has_events=MAX(has_events,?),
                       last_player_id=?,
                       last_seen=?,
                       knowledge_source='hk_maps_import',
                       knowledge_observed_at=?
                   WHERE area_id=? AND building_id=? AND room_count IS NULL""",
                (item["room_count"], int(item["room_count"] > 0), source, now, now,
                 area_id, item["building_id"]),
            )'''
new_preserve='''            if row["room_count"] == item["room_count"] and row["knowledge_source"] == "hk_maps_import":
                preserved += 1
                preserved_ids.append(item["building_id"])
                continue
            cursor = db.execute(
                """UPDATE map_buildings
                   SET room_count=?,
                       has_events=?,
                       last_player_id=?,
                       last_seen=?,
                       knowledge_source='hk_maps_import',
                       knowledge_observed_at=?
                   WHERE area_id=? AND building_id=?""",
                (item["room_count"], int(item["room_count"] > 0), source, now, now,
                 area_id, item["building_id"]),
            )'''
repl(old_preserve,new_preserve,"W3 source overwrite")

# Full live geometry: crystal value comes from the uploaded Full235 source
# table. A live-only building remains visually unknown instead of becoming 0.
old_rows='''        rows=db.execute("""SELECT building_id,room_count,is_invest,faction,building_type
                           FROM map_buildings WHERE area_id=?""",(area_id,)).fetchall()
        known={str(row["building_id"]):dict(row) for row in rows}
        catalog=db.execute("SELECT city,grid FROM hk_maps_catalog WHERE map_key=?",(map_key,)).fetchone()'''
new_rows='''        ensure_hk_map_source_crystals_schema(db)
        rows=db.execute("""SELECT building_id,room_count,is_invest,faction,building_type,knowledge_source
                           FROM map_buildings WHERE area_id=?""",(area_id,)).fetchall()
        known={str(row["building_id"]):dict(row) for row in rows}
        source_rows=db.execute("""SELECT building_id,room_count,is_invest
                                  FROM hk_map_source_crystals WHERE map_key=?""",(map_key,)).fetchall()
        source_known={str(row["building_id"]):dict(row) for row in source_rows}
        catalog=db.execute("SELECT city,grid FROM hk_maps_catalog WHERE map_key=?",(map_key,)).fetchone()'''
repl(old_rows,new_rows,"live geometry source rows")

old_row_block='''        if row:
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
            props["base_color"]=str(props.get("base_color") or props.get("color") or "#4b4b50")'''
new_row_block='''        if row:
            source_row=source_known.get(bid)
            if source_known:
                room=source_row.get("room_count") if source_row is not None else None
                invest=source_row.get("is_invest") if source_row is not None else row.get("is_invest")
            else:
                room=row.get("room_count")
                invest=row.get("is_invest")
            key="NULL" if room is None else str(max(0,min(7,int(room))))
            props["crystals_key"]=key
            props["crystals"]=None if room is None else int(room)
            props["is_investment"]=bool(invest)
            props["crystal_source"]="uploaded_map" if source_row is not None else ("live_unknown" if source_known else "canonical")
            if row.get("faction"):
                props["faction"]=row.get("faction")
            if row.get("building_type"):
                props["building_generator"]=row.get("building_type")
            props["base_color"]=palette.get(key,"#62656b")
        else:
            props["crystals_key"]="NULL"
            props["crystals"]=None
            props["crystal_source"]="live_unknown" if source_known else "canonical_unknown"
            props["base_color"]=str(props.get("base_color") or props.get("color") or "#4b4b50")'''
repl(old_row_block,new_row_block,"live geometry source crystal render")

# Personal Cabinet crystal counters for website-linked maps come from the
# uploaded map catalog, not the mutable shared/live scan.
old_crystals='''    crystals = [
        int(row.get("room0") or 0),
        int(row.get("room1") or 0),
        int(row.get("room2") or 0),
        int(row.get("room3") or 0),
        int(row.get("room4") or 0),
        int(row.get("room5") or 0),
    ]'''
new_crystals='''    canonical_crystals = [
        int(row.get("room0") or 0),
        int(row.get("room1") or 0),
        int(row.get("room2") or 0),
        int(row.get("room3") or 0),
        int(row.get("room4") or 0),
        int(row.get("room5") or 0),
    ]
    source_locked = bool(website.get("key"))
    source_crystals = website.get("crystals") if isinstance(website.get("crystals"), list) else None
    crystals = [int(value or 0) for value in source_crystals[:6]] if source_locked and source_crystals else canonical_crystals
    while len(crystals) < 6:
        crystals.append(0)'''
repl(old_crystals,new_crystals,"cabinet source crystals")

repl(
    '        "invest": int(row.get("invest_count") or 0),\n        "buildings": int(row.get("buildings") or 0),\n        "unknown": int(row.get("unexplored") or 0),',
    '        "invest": int(website.get("invest") if source_locked else (row.get("invest_count") or 0)),\n        "buildings": int(website.get("buildings") if source_locked else (row.get("buildings") or 0)),\n        "unknown": int(website.get("unknown") if source_locked else (row.get("unexplored") or 0)),',
    "cabinet source totals",
)

for marker in (
    "HK_MAP_CRYSTAL_SOURCE_PRIORITY_R1",
    "def ensure_hk_map_source_crystals_schema",
    '"crystal_source": "uploaded_map"',
    "source_known={",
    "WHEN excluded.knowledge_source='hk_maps_import' THEN excluded.room_count",
    "knowledge_source='hk_maps_import'",
):
    if marker not in s:
        raise SystemExit("missing priority marker: "+marker)

TARGET.write_text(s,encoding="utf-8")
print("HK_MAP_CRYSTAL_SOURCE_PRIORITY_R1_PATCH=PASS")
