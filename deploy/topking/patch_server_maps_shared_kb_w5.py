from pathlib import Path

TARGET = Path("/tmp/server.py")
s = TARGET.read_text(encoding="utf-8")

def require(needle: str, message: str) -> None:
    if needle not in s:
        raise SystemExit(message)

# HK_MAP_PROVENANCE_W5_V1
migration_anchor = '''        member_columns = {row["name"] for row in db.execute("PRAGMA table_info(clan_members)")}
        for name, definition in {
            "maps_access": "INTEGER NOT NULL DEFAULT 0",
            "maps_manage": "INTEGER NOT NULL DEFAULT 0",
        }.items():
            if name not in member_columns:
                db.execute(f"ALTER TABLE clan_members ADD COLUMN {name} {definition}")
        now = utc_now()
'''
migration_new = '''        member_columns = {row["name"] for row in db.execute("PRAGMA table_info(clan_members)")}
        for name, definition in {
            "maps_access": "INTEGER NOT NULL DEFAULT 0",
            "maps_manage": "INTEGER NOT NULL DEFAULT 0",
        }.items():
            if name not in member_columns:
                db.execute(f"ALTER TABLE clan_members ADD COLUMN {name} {definition}")
        building_columns = {row["name"] for row in db.execute("PRAGMA table_info(map_buildings)")}
        for name, definition in {
            "knowledge_source": "TEXT NOT NULL DEFAULT 'legacy'",
            "knowledge_observed_at": "INTEGER NOT NULL DEFAULT 0",
        }.items():
            if name not in building_columns:
                db.execute(f"ALTER TABLE map_buildings ADD COLUMN {name} {definition}")
        db.execute("""UPDATE map_buildings
                      SET knowledge_source=CASE
                        WHEN last_player_id='source-hk-maps-import' THEN 'hk_maps_import'
                        WHEN last_player_id LIKE 'anon-%' THEN 'game_live'
                        ELSE 'legacy'
                      END
                      WHERE knowledge_observed_at=0""")
        db.execute("""UPDATE map_buildings
                      SET knowledge_observed_at=last_seen
                      WHERE knowledge_observed_at=0""")
        now = utc_now()
'''
require(migration_anchor, "init_db migration anchor missing")
s = s.replace(migration_anchor, migration_new, 1)

submit_anchor = '''def submit_map_area(player_id: str, value: object) -> dict:
    area, now = normalize_map_area(value), utc_now()
    player_id = contributor_id(player_id)
'''
submit_new = '''# HK_MAP_PROVENANCE_W5_V1
def map_knowledge_source(player_id: str) -> str:
    raw = str(player_id or "").strip()
    if raw == "source-hk-maps-import":
        return "hk_maps_import"
    if raw == "kokkaras-import" or raw == "historical-har" or raw.startswith("source-"):
        return "legacy"
    return "game_live"


def submit_map_area(player_id: str, value: object) -> dict:
    area, now = normalize_map_area(value), utc_now()
    knowledge_source = map_knowledge_source(player_id)
    player_id = contributor_id(player_id)
'''
require(submit_anchor, "submit_map_area start anchor missing")
s = s.replace(submit_anchor, submit_new, 1)

complete_anchor = '''            if total and known >= total:
                return {"ok":True,"area_id":canonical_id,"source_area_id":area["area_id"],"ignored_complete":True,
                        "progress":progress,"buildings":total,"added_buildings":0,"enriched_buildings":0}
'''
complete_new = '''            if total and known >= total and knowledge_source != "game_live":
                return {"ok":True,"area_id":canonical_id,"source_area_id":area["area_id"],"ignored_complete":True,
                        "progress":progress,"buildings":total,"added_buildings":0,"enriched_buildings":0}
'''
require(complete_anchor, "complete-map early return anchor missing")
s = s.replace(complete_anchor, complete_new, 1)

before_anchor = '''            before = db.execute("SELECT opened,room_count,has_events,is_invest,tier,faction,building_type FROM map_buildings WHERE area_id=? AND building_id=?",
                                (canonical_id, row["building_id"])).fetchone()
'''
before_new = '''            before = db.execute("""SELECT opened,room_count,has_events,is_invest,tier,faction,building_type,
                                         knowledge_source,knowledge_observed_at
                                  FROM map_buildings WHERE area_id=? AND building_id=?""",
                                (canonical_id, row["building_id"])).fetchone()
'''
require(before_anchor, "submit pre-update select anchor missing")
s = s.replace(before_anchor, before_new, 1)

enriched_anchor = '''            elif ((before["room_count"] is None and row["room_count"] is not None) or
                  (not before["opened"] and row["opened"]) or (before["tier"] is None and row["tier"] is not None) or
                  (not before["faction"] and row["faction"]) or (not before["building_type"] and row["building_type"])):
                enriched += 1
'''
enriched_new = '''            elif ((before["room_count"] is None and row["room_count"] is not None) or
                  (knowledge_source == "game_live" and row["room_count"] is not None and before["room_count"] != row["room_count"]) or
                  (not before["opened"] and row["opened"]) or (before["tier"] is None and row["tier"] is not None) or
                  (not before["faction"] and row["faction"]) or (not before["building_type"] and row["building_type"])):
                enriched += 1
'''
require(enriched_anchor, "enriched counter anchor missing")
s = s.replace(enriched_anchor, enriched_new, 1)

upsert_anchor = '''            db.execute("""INSERT INTO map_buildings(area_id,building_id,opened,room_count,has_events,is_invest,tier,faction,building_type,last_player_id,last_seen)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(area_id,building_id) DO UPDATE SET
                        opened=MAX(map_buildings.opened,excluded.opened),room_count=COALESCE(map_buildings.room_count,excluded.room_count),
                        has_events=MAX(map_buildings.has_events,excluded.has_events),is_invest=MAX(map_buildings.is_invest,excluded.is_invest),
                        tier=COALESCE(map_buildings.tier,excluded.tier),faction=CASE WHEN map_buildings.faction='' THEN excluded.faction ELSE map_buildings.faction END,
                        building_type=CASE WHEN map_buildings.building_type='' THEN excluded.building_type ELSE map_buildings.building_type END,
                        last_player_id=CASE WHEN map_buildings.room_count IS NULL AND excluded.room_count IS NOT NULL THEN excluded.last_player_id ELSE map_buildings.last_player_id END,
                        last_seen=MAX(map_buildings.last_seen,excluded.last_seen)""",
                       (canonical_id,row["building_id"],int(row["opened"]),row["room_count"],int(row["has_events"]),int(row["is_invest"]),
                        row["tier"],row["faction"],row["building_type"],player_id,now))
'''
upsert_new = '''            db.execute("""INSERT INTO map_buildings(
                            area_id,building_id,opened,room_count,has_events,is_invest,tier,faction,building_type,
                            last_player_id,last_seen,knowledge_source,knowledge_observed_at)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(area_id,building_id) DO UPDATE SET
                        opened=MAX(map_buildings.opened,excluded.opened),
                        room_count=CASE
                          WHEN excluded.room_count IS NULL THEN map_buildings.room_count
                          WHEN excluded.knowledge_source='game_live' THEN excluded.room_count
                          WHEN map_buildings.room_count IS NULL THEN excluded.room_count
                          ELSE map_buildings.room_count END,
                        has_events=CASE
                          WHEN excluded.room_count IS NOT NULL
                           AND (excluded.knowledge_source='game_live' OR map_buildings.room_count IS NULL)
                          THEN excluded.has_events
                          ELSE MAX(map_buildings.has_events,excluded.has_events) END,
                        is_invest=MAX(map_buildings.is_invest,excluded.is_invest),
                        tier=COALESCE(map_buildings.tier,excluded.tier),
                        faction=CASE WHEN map_buildings.faction='' THEN excluded.faction ELSE map_buildings.faction END,
                        building_type=CASE WHEN map_buildings.building_type='' THEN excluded.building_type ELSE map_buildings.building_type END,
                        last_player_id=CASE
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
                          THEN excluded.knowledge_observed_at ELSE map_buildings.knowledge_observed_at END""",
                       (canonical_id,row["building_id"],int(row["opened"]),row["room_count"],int(row["has_events"]),int(row["is_invest"]),
                        row["tier"],row["faction"],row["building_type"],player_id,now,knowledge_source,now))
'''
require(upsert_anchor, "submit map_buildings upsert anchor missing")
s = s.replace(upsert_anchor, upsert_new, 1)

import_select = '''                """SELECT room_count FROM map_buildings
                   WHERE area_id=? AND building_id=?""",
'''
import_select_new = '''                """SELECT room_count,knowledge_source,knowledge_observed_at FROM map_buildings
                   WHERE area_id=? AND building_id=?""",
'''
require(import_select, "W3 import select anchor missing")
s = s.replace(import_select, import_select_new, 1)

import_update = '''                """UPDATE map_buildings
                   SET room_count=?,
                       has_events=MAX(has_events,?),
                       last_player_id=?,
                       last_seen=?
                   WHERE area_id=? AND building_id=? AND room_count IS NULL""",
                (item["room_count"], int(item["room_count"] > 0), source, now,
                 area_id, item["building_id"]),
'''
import_update_new = '''                """UPDATE map_buildings
                   SET room_count=?,
                       has_events=MAX(has_events,?),
                       last_player_id=?,
                       last_seen=?,
                       knowledge_source='hk_maps_import',
                       knowledge_observed_at=?
                   WHERE area_id=? AND building_id=? AND room_count IS NULL""",
                (item["room_count"], int(item["room_count"] > 0), source, now, now,
                 area_id, item["building_id"]),
'''
require(import_update, "W3 import update anchor missing")
s = s.replace(import_update, import_update_new, 1)

return_anchor = '''        "source": source,
    }
'''
return_new = '''        "source": source,
        "knowledge_source": "hk_maps_import",
    }
'''
require(return_anchor, "W3 import return anchor missing")
s = s.replace(return_anchor, return_new, 1)

detail_anchor = '''        buildings=[dict(row) for row in db.execute("SELECT building_id,opened,room_count,has_events,is_invest,tier,faction,building_type FROM map_buildings WHERE area_id=? ORDER BY building_id",(area_id,))]
'''
detail_new = '''        buildings=[dict(row) for row in db.execute(
            """SELECT building_id,opened,room_count,has_events,is_invest,tier,faction,building_type,
                      knowledge_source,knowledge_observed_at
               FROM map_buildings WHERE area_id=? ORDER BY building_id""",(area_id,))]
'''
require(detail_anchor, "map_detail anchor missing")
s = s.replace(detail_anchor, detail_new, 1)

for marker in (
    "HK_MAP_PROVENANCE_W5_V1",
    "knowledge_source",
    "knowledge_observed_at",
    "def map_knowledge_source",
    "knowledge_source != \"game_live\"",
    "'hk_maps_import'",
):
    require(marker, "missing W5 marker: " + marker)


merge_anchor = '''                    db.execute("""INSERT INTO map_buildings(area_id,building_id,opened,room_count,has_events,is_invest,tier,faction,building_type,last_player_id,last_seen)
                                VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(area_id,building_id) DO UPDATE SET
                                opened=MAX(map_buildings.opened,excluded.opened),room_count=COALESCE(map_buildings.room_count,excluded.room_count),
                                has_events=MAX(map_buildings.has_events,excluded.has_events),is_invest=MAX(map_buildings.is_invest,excluded.is_invest),
                                tier=COALESCE(map_buildings.tier,excluded.tier),faction=CASE WHEN map_buildings.faction='' THEN excluded.faction ELSE map_buildings.faction END,
                                building_type=CASE WHEN map_buildings.building_type='' THEN excluded.building_type ELSE map_buildings.building_type END,
                                last_player_id=CASE WHEN map_buildings.room_count IS NULL AND excluded.room_count IS NOT NULL THEN excluded.last_player_id ELSE map_buildings.last_player_id END,
                                last_seen=MAX(map_buildings.last_seen,excluded.last_seen)""",
                               (winner,row["building_id"],row["opened"],row["room_count"],row["has_events"],row["is_invest"],row["tier"],
                                row["faction"],row["building_type"],row["last_player_id"],row["last_seen"]))
'''
merge_new = '''                    db.execute("""INSERT INTO map_buildings(
                                area_id,building_id,opened,room_count,has_events,is_invest,tier,faction,building_type,
                                last_player_id,last_seen,knowledge_source,knowledge_observed_at)
                                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(area_id,building_id) DO UPDATE SET
                                opened=MAX(map_buildings.opened,excluded.opened),
                                room_count=CASE
                                  WHEN excluded.room_count IS NULL THEN map_buildings.room_count
                                  WHEN map_buildings.room_count IS NULL THEN excluded.room_count
                                  WHEN excluded.knowledge_source='game_live'
                                   AND (map_buildings.knowledge_source<>'game_live'
                                        OR excluded.knowledge_observed_at>map_buildings.knowledge_observed_at)
                                  THEN excluded.room_count
                                  ELSE map_buildings.room_count END,
                                has_events=CASE
                                  WHEN excluded.room_count IS NOT NULL
                                   AND (map_buildings.room_count IS NULL
                                        OR (excluded.knowledge_source='game_live'
                                            AND (map_buildings.knowledge_source<>'game_live'
                                                 OR excluded.knowledge_observed_at>map_buildings.knowledge_observed_at)))
                                  THEN excluded.has_events
                                  ELSE MAX(map_buildings.has_events,excluded.has_events) END,
                                is_invest=MAX(map_buildings.is_invest,excluded.is_invest),
                                tier=COALESCE(map_buildings.tier,excluded.tier),
                                faction=CASE WHEN map_buildings.faction='' THEN excluded.faction ELSE map_buildings.faction END,
                                building_type=CASE WHEN map_buildings.building_type='' THEN excluded.building_type ELSE map_buildings.building_type END,
                                last_player_id=CASE
                                  WHEN excluded.room_count IS NOT NULL
                                   AND (map_buildings.room_count IS NULL
                                        OR (excluded.knowledge_source='game_live'
                                            AND (map_buildings.knowledge_source<>'game_live'
                                                 OR excluded.knowledge_observed_at>map_buildings.knowledge_observed_at)))
                                  THEN excluded.last_player_id ELSE map_buildings.last_player_id END,
                                last_seen=MAX(map_buildings.last_seen,excluded.last_seen),
                                knowledge_source=CASE
                                  WHEN excluded.room_count IS NOT NULL
                                   AND (map_buildings.room_count IS NULL
                                        OR (excluded.knowledge_source='game_live'
                                            AND (map_buildings.knowledge_source<>'game_live'
                                                 OR excluded.knowledge_observed_at>map_buildings.knowledge_observed_at)))
                                  THEN excluded.knowledge_source ELSE map_buildings.knowledge_source END,
                                knowledge_observed_at=CASE
                                  WHEN excluded.room_count IS NOT NULL
                                   AND (map_buildings.room_count IS NULL
                                        OR (excluded.knowledge_source='game_live'
                                            AND (map_buildings.knowledge_source<>'game_live'
                                                 OR excluded.knowledge_observed_at>map_buildings.knowledge_observed_at)))
                                  THEN excluded.knowledge_observed_at ELSE map_buildings.knowledge_observed_at END""",
                               (winner,row["building_id"],row["opened"],row["room_count"],row["has_events"],row["is_invest"],row["tier"],
                                row["faction"],row["building_type"],row["last_player_id"],row["last_seen"],
                                row["knowledge_source"],row["knowledge_observed_at"]))
'''
require(merge_anchor, "merge provenance anchor missing")
s = s.replace(merge_anchor, merge_new, 1)

TARGET.write_text(s, encoding="utf-8")
