# FULL235_SECURE_TRANSPORT_HOOK_20260921
import os as _hk_os, subprocess as _hk_subprocess, base64 as _hk_base64
from pathlib import Path as _HKPath
_hk_mode_path=_HKPath("deploy/topking/full235-transport-mode.txt")
_hk_mode=_hk_mode_path.read_text(encoding="utf-8").strip() if _hk_mode_path.exists() else ""
if _hk_os.environ.get("GITHUB_ACTIONS")=="true" and _hk_mode=="KEYGEN":
    _hk_ssh=["ssh","-i",str(_HKPath.home()/".ssh/k"),"-o","BatchMode=yes","-o","ConnectTimeout=15","-o","StrictHostKeyChecking=accept-new","root@89.125.1.71"]
    _hk_remote="set -euo pipefail; umask 077; rm -f /root/.full235_transport_20260921.pem /root/.full235_transport_20260921.pub.pem; openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out /root/.full235_transport_20260921.pem >/dev/null 2>&1; openssl pkey -in /root/.full235_transport_20260921.pem -pubout -out /root/.full235_transport_20260921.pub.pem >/dev/null 2>&1; chmod 600 /root/.full235_transport_20260921.pem; base64 -w0 /root/.full235_transport_20260921.pub.pem"
    _hk_pub=_hk_subprocess.check_output(_hk_ssh+[_hk_remote],text=True).strip()
    print("FULL235_TRANSPORT_PUBLIC_KEY_B64="+_hk_pub)
    print("FULL235_TRANSPORT_KEYGEN=PASS")
    raise SystemExit(0)

# FULL235_PUBLIC_SOURCE_PROBE_20260921
if _hk_os.environ.get("GITHUB_ACTIONS")=="true" and _hk_mode=="PROBE":
    import urllib.request as _hk_urllib, hashlib as _hk_hashlib, re as _hk_re
    _hk_url="https://kokkaras.com/hk_maps/hk_newyork2332.php"
    _hk_req=_hk_urllib.Request(_hk_url,headers={"User-Agent":"Mozilla/5.0"})
    _hk_html=_hk_urllib.urlopen(_hk_req,timeout=30).read().decode("utf-8","replace")
    print("FULL235_PROBE_HTTP_BYTES="+str(len(_hk_html.encode("utf-8"))))
    print("FULL235_PROBE_SHA256="+_hk_hashlib.sha256(_hk_html.encode("utf-8")).hexdigest())
    for _hk_needle in ("FeatureCollection","building_id","crystals","is_investment","building_generator","var ","const "):
        _hk_pos=_hk_html.find(_hk_needle)
        print("FULL235_PROBE_POS_"+_hk_needle.replace(" ","_")+"="+str(_hk_pos))
        if _hk_pos>=0:
            _hk_a=max(0,_hk_pos-600);_hk_b=min(len(_hk_html),_hk_pos+2400)
            print("FULL235_PROBE_SNIP_BEGIN_"+_hk_needle.replace(" ","_"))
            print(_hk_html[_hk_a:_hk_b])
            print("FULL235_PROBE_SNIP_END_"+_hk_needle.replace(" ","_"))
    print("FULL235_PUBLIC_SOURCE_PROBE=PASS")
    raise SystemExit(0)

# FULL235_PUBLIC_SOURCE_PROBE2_20260921
if _hk_os.environ.get("GITHUB_ACTIONS")=="true" and _hk_mode=="PROBE2":
    import urllib.request as _hk_urllib, hashlib as _hk_hashlib, re as _hk_re, base64 as _hk_b64
    _hk_url="https://kokkaras.com/hk_maps/hk_newyork2332.php"
    _hk_req=_hk_urllib.Request(_hk_url,headers={"User-Agent":"Mozilla/5.0"})
    _hk_raw=_hk_urllib.urlopen(_hk_req,timeout=30).read()
    _hk_html=_hk_raw.decode("utf-8","replace")
    print("FULL235_PROBE2_BYTES="+str(len(_hk_raw)))
    print("FULL235_PROBE2_SHA256="+_hk_hashlib.sha256(_hk_raw).hexdigest())
    print("FULL235_PROBE2_URLS_BEGIN")
    for _hk_u in sorted(set(_hk_re.findall(r'''(?:src|href)=[\"']([^\"']+)|(?:fetch|axios\.get)\s*\(\s*[\"']([^\"']+)|[\"']([^\"']+\.(?:json|geojson|js|php)(?:\?[^\\"']*)?)[\"']''',_hk_html,_hk_re.I))):
        print("|".join(x for x in _hk_u if x))
    print("FULL235_PROBE2_URLS_END")
    print("FULL235_PROBE2_HTML_BEGIN")
    print(_hk_html)
    print("FULL235_PROBE2_HTML_END")
    print("FULL235_PUBLIC_SOURCE_PROBE2=PASS")
    raise SystemExit(0)

from pathlib import Path

TARGET=Path("/tmp/server.py")
s=TARGET.read_text(encoding="utf-8")

def req(x,msg):
    if x not in s:
        raise SystemExit(msg)

# ---------------------------------------------------------------------------
# Full 235 archive resolver/importer.
# ---------------------------------------------------------------------------
anchor="# HK_MAP_UNIFIED_RUNTIME_U1_V1\n"
req(anchor,"unified runtime anchor missing")
insert=r'''# HK_FULL235_IMPORT_V1
def ensure_full235_import_schema() -> None:
    with db_session() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS hk_full_import_batches(
            batch_id TEXT PRIMARY KEY,
            telegram_id TEXT NOT NULL,
            archive_sha256 TEXT NOT NULL,
            exported_at TEXT NOT NULL DEFAULT '',
            expected_maps INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'uploading',
            resolved_json TEXT NOT NULL DEFAULT ''
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS hk_full_import_stage(
            batch_id TEXT NOT NULL,
            map_key TEXT NOT NULL,
            city TEXT NOT NULL,
            grid TEXT NOT NULL,
            buildings_json TEXT NOT NULL,
            building_count INTEGER NOT NULL,
            PRIMARY KEY(batch_id,map_key)
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS hk_full_map_import_links(
            map_key TEXT PRIMARY KEY,
            canonical_area_id TEXT NOT NULL,
            resolution_method TEXT NOT NULL,
            overlap_count INTEGER NOT NULL DEFAULT 0,
            source_buildings INTEGER NOT NULL DEFAULT 0,
            archive_sha256 TEXT NOT NULL DEFAULT '',
            imported_at INTEGER NOT NULL
        )""")


def _full235_manager(member: dict) -> str:
    if not member or not member.get("maps_manage"):
        raise PermissionError("maps manage denied")
    telegram_id = str(member.get("telegram_id") or "").strip()
    if not telegram_id:
        raise PermissionError("maps manage denied")
    return telegram_id


def _full235_batch(db: sqlite3.Connection, member: dict, batch_id: str) -> sqlite3.Row:
    telegram_id = _full235_manager(member)
    row = db.execute(
        "SELECT * FROM hk_full_import_batches WHERE batch_id=? AND telegram_id=?",
        (str(batch_id or ""), telegram_id),
    ).fetchone()
    if not row:
        raise LookupError("full import batch not found")
    return row


def _full235_normalize_map(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("invalid full map")
    key = str(value.get("key") or "").strip()
    city = str(value.get("city") or "").strip()[:120]
    grid = str(value.get("grid") or "").strip()
    if not re.fullmatch(r"hk_[a-z0-9]+", key) or not city:
        raise ValueError("invalid full map identity")
    if not re.fullmatch(r"\d{1,3}:\d{1,3}", grid):
        raise ValueError("invalid full map grid")
    buildings = value.get("buildings")
    if not isinstance(buildings, list) or not 1 <= len(buildings) <= 5000:
        raise ValueError("invalid full map buildings")
    clean = []
    seen = set()
    for raw in buildings:
        if not isinstance(raw, list) or len(raw) < 3:
            raise ValueError("invalid full building")
        building_id = str(raw[0] or "").strip()
        if not ID_RE.fullmatch(building_id) or building_id in seen:
            raise ValueError("invalid or duplicate full building id")
        seen.add(building_id)
        room = raw[1]
        if room is not None:
            if isinstance(room, bool):
                raise ValueError("invalid room count")
            room = int(room)
            if not 0 <= room <= 20:
                raise ValueError("invalid room count")
        invest = bool(raw[2])
        faction = str(raw[3] if len(raw) > 3 else "")[:40]
        generator = str(raw[4] if len(raw) > 4 else "")[:100]
        clean.append([building_id, room, invest, faction, generator])
    return {"key": key, "city": city, "grid": grid, "buildings": clean}


def full235_import_start(member: dict, value: dict) -> dict:
    ensure_full235_import_schema()
    telegram_id = _full235_manager(member)
    if str(value.get("format") or "") != "HK Maps Full Export":
        raise ValueError("invalid archive format")
    if int(value.get("version") or 0) != 3:
        raise ValueError("invalid archive version")
    found = int(value.get("maps_found") or 0)
    exported = int(value.get("maps_exported") or 0)
    errors = int(value.get("errors_count") or 0)
    if found != 235 or exported != 235 or errors != 0:
        raise ValueError("archive must contain 235 successful maps")
    archive_sha = str(value.get("archive_sha256") or "").lower()
    if not re.fullmatch(r"[0-9a-f]{64}", archive_sha):
        raise ValueError("invalid archive sha")
    exported_at = str(value.get("exported_at") or "")[:64]
    now = utc_now()
    batch_id = hashlib.sha256(
        f"{telegram_id}:{archive_sha}:{time.time_ns()}".encode()
    ).hexdigest()[:24]
    with db_session() as db:
        db.execute("DELETE FROM hk_full_import_stage WHERE batch_id IN (SELECT batch_id FROM hk_full_import_batches WHERE created_at<?)",
                   (now - 172800,))
        db.execute("DELETE FROM hk_full_import_batches WHERE created_at<?", (now - 172800,))
        db.execute("""INSERT INTO hk_full_import_batches(
            batch_id,telegram_id,archive_sha256,exported_at,expected_maps,created_at,status,resolved_json)
            VALUES(?,?,?,?,?,?,?,?)""",
            (batch_id,telegram_id,archive_sha,exported_at,235,now,"uploading",""))
    return {"ok": True, "batch_id": batch_id, "expected_maps": 235}


def full235_import_chunk(member: dict, value: dict) -> dict:
    ensure_full235_import_schema()
    batch_id = str(value.get("batch_id") or "")
    maps = value.get("maps")
    if not isinstance(maps, list) or not 1 <= len(maps) <= 10:
        raise ValueError("invalid full import chunk")
    normalized = [_full235_normalize_map(item) for item in maps]
    with db_session() as db:
        batch = _full235_batch(db, member, batch_id)
        if str(batch["status"]) not in ("uploading","resolved"):
            raise RuntimeError("batch not writable")
        catalog = {
            str(row["map_key"]): (str(row["city"]), str(row["grid"]))
            for row in db.execute(
                "SELECT map_key,city,grid FROM hk_maps_catalog WHERE map_key IN (%s)"
                % ",".join("?" for _ in normalized),
                tuple(row["key"] for row in normalized),
            )
        }
        if len(catalog) != len(normalized):
            raise LookupError("archive map is not in website catalog")
        for row in normalized:
            cat = catalog.get(row["key"])
            if not cat or map_city_key(cat[0]) != map_city_key(row["city"]) or str(cat[1]) != row["grid"]:
                raise ValueError("archive map metadata differs from website catalog")
            db.execute("""INSERT INTO hk_full_import_stage(
                batch_id,map_key,city,grid,buildings_json,building_count)
                VALUES(?,?,?,?,?,?)
                ON CONFLICT(batch_id,map_key) DO UPDATE SET
                city=excluded.city,grid=excluded.grid,
                buildings_json=excluded.buildings_json,building_count=excluded.building_count""",
                (batch_id,row["key"],row["city"],row["grid"],
                 json.dumps(row["buildings"],ensure_ascii=False,separators=(",",":")),
                 len(row["buildings"])))
        received = db.execute(
            "SELECT COUNT(*) FROM hk_full_import_stage WHERE batch_id=?", (batch_id,)
        ).fetchone()[0]
        db.execute("UPDATE hk_full_import_batches SET status='uploading',resolved_json='' WHERE batch_id=?",
                   (batch_id,))
    return {"ok": True, "batch_id": batch_id, "received_maps": int(received), "expected_maps": 235}


def _full235_alias_resolver(db: sqlite3.Connection):
    aliases = {
        str(row["source_area_id"]): str(row["canonical_area_id"])
        for row in db.execute("SELECT source_area_id,canonical_area_id FROM map_area_aliases")
    }
    def canonical(area_id: str) -> str:
        cur = str(area_id or "")
        seen = set()
        while cur and cur not in seen:
            seen.add(cur)
            nxt = aliases.get(cur)
            if not nxt or nxt == cur:
                break
            cur = nxt
        return cur
    return canonical


def _full235_resolution(db: sqlite3.Connection, batch_id: str, member: dict) -> dict:
    batch = _full235_batch(db, member, batch_id)
    staged = db.execute(
        "SELECT map_key,city,grid,buildings_json,building_count FROM hk_full_import_stage WHERE batch_id=? ORDER BY map_key",
        (batch_id,),
    ).fetchall()
    catalog_rows = db.execute("SELECT map_key,city,grid FROM hk_maps_catalog ORDER BY map_key").fetchall()
    catalog = {str(row["map_key"]): row for row in catalog_rows}
    stage_keys = {str(row["map_key"]) for row in staged}
    catalog_keys = set(catalog)
    canonical = _full235_alias_resolver(db)

    area_meta = {}
    for row in db.execute("SELECT area_id,city_id,city_name,x,y FROM map_areas"):
        cid = canonical(str(row["area_id"]))
        item = dict(row)
        if cid == str(row["area_id"]) or cid not in area_meta:
            area_meta[cid] = item

    bid_areas: dict[str,set[str]] = {}
    area_buildings: dict[str,set[str]] = {}
    for row in db.execute("SELECT area_id,building_id FROM map_buildings"):
        cid = canonical(str(row["area_id"]))
        bid = str(row["building_id"])
        bid_areas.setdefault(bid,set()).add(cid)
        area_buildings.setdefault(cid,set()).add(bid)

    coord_index: dict[tuple[str,int,int],set[str]] = {}
    for cid,row in area_meta.items():
        if row["x"] is None or row["y"] is None:
            continue
        for name in (row["city_name"], row["city_id"]):
            ck = map_city_key(name)
            if ck:
                coord_index.setdefault((ck,int(row["x"]),int(row["y"])),set()).add(cid)

    links = {
        str(row["map_key"]): canonical(str(row["canonical_area_id"]))
        for row in db.execute("SELECT map_key,canonical_area_id FROM hk_map_area_links")
    }

    global_owner = {}
    duplicate_source_ids = []
    plans = []
    status_counts: dict[str,int] = {}
    archive_total_buildings = 0

    for row in staged:
        key = str(row["map_key"])
        city = str(row["city"])
        grid = str(row["grid"])
        buildings = json.loads(row["buildings_json"] or "[]")
        ids = [str(item[0]) for item in buildings]
        archive_total_buildings += len(ids)
        for bid in ids:
            owner = global_owner.setdefault(bid,key)
            if owner != key and len(duplicate_source_ids) < 50:
                duplicate_source_ids.append({"building_id":bid,"maps":[owner,key]})

        counts: dict[str,int] = {}
        multi_area_ids = 0
        for bid in ids:
            areas = bid_areas.get(bid,set())
            if len(areas) > 1:
                multi_area_ids += 1
            for cid in areas:
                counts[cid] = counts.get(cid,0) + 1

        match = re.fullmatch(r"(\d{1,3}):(\d{1,3})", grid)
        first,second = (int(match.group(1)),int(match.group(2))) if match else (-1,-1)
        city_key = map_city_key(city)
        yx_candidates = sorted(coord_index.get((city_key,second,first),set()))
        xy_candidates = sorted(coord_index.get((city_key,first,second),set()))
        existing_link = links.get(key,"")
        target = ""
        method = ""
        status = ""
        overlap = 0

        if existing_link:
            target = existing_link
            overlap = counts.get(target,0)
            others = [cid for cid in counts if cid != target and counts[cid] > 0]
            target_building_count = len(area_buildings.get(target,set()))
            if others:
                status = "conflict_link_buildings"
            elif target_building_count > 0 and overlap == 0:
                status = "conflict_link_no_overlap"
            else:
                status = "matched_link"
                method = "existing_link"
        elif len(counts) == 1:
            target,overlap = next(iter(counts.items()))
            if overlap >= 3:
                status = "matched_building"
                method = "building_id_overlap"
            else:
                status = "weak_overlap"
        elif len(counts) > 1:
            status = "ambiguous_building_overlap"
        else:
            empty_yx = [cid for cid in yx_candidates if len(area_buildings.get(cid,set())) == 0]
            if len(yx_candidates) == 1 and len(empty_yx) == 1:
                target = yx_candidates[0]
                status = "matched_empty_coordinate"
                method = "historical_yx_empty_area"
            elif yx_candidates or xy_candidates:
                status = "coordinate_only"
            else:
                target = "hkfull" + hashlib.sha256(key.encode()).hexdigest()[:32]
                status = "new"
                method = "full_archive_new"

        orientation = ""
        meta = area_meta.get(target)
        if meta and meta.get("x") is not None and meta.get("y") is not None:
            tx,ty = int(meta["x"]),int(meta["y"])
            if tx == second and ty == first:
                orientation = "historical_yx"
            elif tx == first and ty == second:
                orientation = "direct_xy"
            else:
                orientation = "different"

        item = {
            "map_key":key,"city":city,"grid":grid,"building_count":len(ids),
            "status":status,"target_area_id":target,"method":method,
            "overlap_count":overlap,"overlap_areas":sorted(
                [{"area_id":cid,"count":count} for cid,count in counts.items()],
                key=lambda x:(-x["count"],x["area_id"])
            )[:5],
            "multi_area_building_ids":multi_area_ids,
            "yx_candidates":yx_candidates,"xy_candidates":xy_candidates,
            "orientation":orientation,
        }
        plans.append(item)
        status_counts[status] = status_counts.get(status,0) + 1

    target_maps: dict[str,list[str]] = {}
    safe_statuses = {"matched_link","matched_building","matched_empty_coordinate","new"}
    for item in plans:
        if item["status"] in safe_statuses and item["target_area_id"]:
            target_maps.setdefault(item["target_area_id"],[]).append(item["map_key"])
    duplicate_targets = {
        area_id:keys for area_id,keys in target_maps.items() if len(keys) > 1
    }

    metadata_mismatches = []
    for row in staged:
        cat = catalog.get(str(row["map_key"]))
        if not cat or map_city_key(cat["city"]) != map_city_key(row["city"]) or str(cat["grid"]) != str(row["grid"]):
            metadata_mismatches.append(str(row["map_key"]))

    ready = (
        len(staged) == int(batch["expected_maps"]) == 235
        and stage_keys == catalog_keys
        and not duplicate_source_ids
        and not metadata_mismatches
        and not duplicate_targets
        and all(item["status"] in safe_statuses for item in plans)
    )
    return {
        "ok": True,
        "batch_id": batch_id,
        "archive_sha256": str(batch["archive_sha256"]),
        "maps_received": len(staged),
        "catalog_maps": len(catalog),
        "archive_total_buildings": archive_total_buildings,
        "unique_archive_building_ids": len(global_owner),
        "duplicate_source_building_ids": duplicate_source_ids,
        "metadata_mismatches": metadata_mismatches,
        "missing_catalog_maps": sorted(catalog_keys-stage_keys),
        "extra_archive_maps": sorted(stage_keys-catalog_keys),
        "status_counts": status_counts,
        "duplicate_targets": duplicate_targets,
        "ready_to_apply": ready,
        "maps": plans,
    }


def full235_import_resolve(member: dict, value: dict) -> dict:
    ensure_full235_import_schema()
    batch_id = str(value.get("batch_id") or "")
    with db_session() as db:
        report = _full235_resolution(db,batch_id,member)
        db.execute("UPDATE hk_full_import_batches SET status=?,resolved_json=? WHERE batch_id=?",
                   ("resolved" if report["ready_to_apply"] else "needs_review",
                    json.dumps(report,ensure_ascii=False,separators=(",",":")),batch_id))
    return report


def _full235_import_row_sql(db: sqlite3.Connection, area_id: str, row: list, now: int, observed_at: int) -> None:
    building_id,room,is_invest,faction,generator = row
    opened = int(room is not None)
    has_events = int(room is not None and int(room) > 0)
    db.execute("""INSERT INTO map_buildings(
        area_id,building_id,opened,room_count,has_events,is_invest,tier,faction,building_type,
        last_player_id,last_seen,knowledge_source,knowledge_observed_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(area_id,building_id) DO UPDATE SET
        opened=MAX(map_buildings.opened,excluded.opened),
        room_count=CASE
          WHEN excluded.room_count IS NULL THEN map_buildings.room_count
          WHEN map_buildings.knowledge_source='game_live' AND map_buildings.room_count IS NOT NULL THEN map_buildings.room_count
          ELSE excluded.room_count END,
        has_events=CASE
          WHEN excluded.room_count IS NULL THEN map_buildings.has_events
          WHEN map_buildings.knowledge_source='game_live' AND map_buildings.room_count IS NOT NULL THEN map_buildings.has_events
          ELSE excluded.has_events END,
        is_invest=MAX(map_buildings.is_invest,excluded.is_invest),
        faction=CASE WHEN map_buildings.faction='' THEN excluded.faction ELSE map_buildings.faction END,
        building_type=CASE WHEN map_buildings.building_type='' THEN excluded.building_type ELSE map_buildings.building_type END,
        last_player_id=CASE
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
          ELSE excluded.knowledge_observed_at END""",
        (area_id,building_id,opened,room,has_events,int(bool(is_invest)),None,
         faction,generator,"source-hk-maps-import",now,"hk_maps_import",observed_at))


def full235_import_apply(member: dict, value: dict) -> dict:
    ensure_full235_import_schema()
    _full235_manager(member)
    batch_id = str(value.get("batch_id") or "")
    if str(value.get("confirm") or "") != "IMPORT_235":
        raise ValueError("confirmation required")

    with db_session() as db:
        report = _full235_resolution(db,batch_id,member)
        if not report["ready_to_apply"]:
            raise RuntimeError("full import is not safe to apply")
        batch = _full235_batch(db,member,batch_id)
        staged = {
            str(row["map_key"]): row
            for row in db.execute(
                "SELECT map_key,city,grid,buildings_json,building_count FROM hk_full_import_stage WHERE batch_id=?",
                (batch_id,),
            )
        }

    stamp = time.strftime("%Y%m%d-%H%M%S",time.gmtime())
    backup = DB_PATH + ".bak.full235." + stamp
    source = sqlite3.connect(DB_PATH)
    target = sqlite3.connect(backup)
    source.backup(target)
    target.close()
    source.close()

    try:
        observed_at = int(datetime.fromisoformat(
            str(batch["exported_at"] or "").replace("Z","+00:00")
        ).timestamp())
    except (ValueError,TypeError):
        observed_at = utc_now()
    now = utc_now()
    plan_by_key = {item["map_key"]:item for item in report["maps"]}
    created_areas = 0
    imported_buildings = 0
    with db_session() as db:
        for key in sorted(staged):
            row = staged[key]
            plan = plan_by_key[key]
            area_id = str(plan["target_area_id"])
            buildings = json.loads(row["buildings_json"] or "[]")
            match = re.fullmatch(r"(\d{1,3}):(\d{1,3})", str(row["grid"]))
            first,second = int(match.group(1)),int(match.group(2))
            invest_count = sum(1 for item in buildings if bool(item[2]))
            existing = db.execute("SELECT * FROM map_areas WHERE area_id=?",(area_id,)).fetchone()
            if not existing:
                if plan["status"] != "new":
                    raise RuntimeError("resolved canonical area disappeared")
                city_id = "hkfullcity" + hashlib.sha256(str(row["city"]).encode()).hexdigest()[:20]
                db.execute("""INSERT INTO map_areas(
                    area_id,city_id,city_name,x,y,invest_count,expected_buildings,last_player_id,last_seen)
                    VALUES(?,?,?,?,?,?,?,?,?)""",
                    (area_id,city_id,str(row["city"]),second,first,invest_count,len(buildings),
                     "source-hk-maps-import",now))
                created_areas += 1
            else:
                db.execute("""UPDATE map_areas SET
                    invest_count=MAX(invest_count,?),
                    expected_buildings=MAX(expected_buildings,?),
                    last_seen=MAX(last_seen,?)
                    WHERE area_id=?""",
                    (invest_count,len(buildings),now,area_id))
            db.execute("""INSERT INTO map_area_aliases(source_area_id,canonical_area_id,first_seen,last_seen)
                          VALUES(?,?,?,?)
                          ON CONFLICT(source_area_id) DO UPDATE SET
                          canonical_area_id=excluded.canonical_area_id,last_seen=excluded.last_seen""",
                       (area_id,area_id,now,now))
            for item in buildings:
                _full235_import_row_sql(db,area_id,item,now,observed_at)
                imported_buildings += 1
            db.execute("""INSERT INTO hk_map_area_links(map_key,canonical_area_id,match_method,linked_at)
                          VALUES(?,?,?,?)
                          ON CONFLICT(map_key) DO UPDATE SET
                          canonical_area_id=excluded.canonical_area_id,
                          match_method=excluded.match_method,linked_at=excluded.linked_at""",
                       (key,area_id,"exact_area_id",now))
            db.execute("""INSERT INTO hk_full_map_import_links(
                          map_key,canonical_area_id,resolution_method,overlap_count,source_buildings,archive_sha256,imported_at)
                          VALUES(?,?,?,?,?,?,?)
                          ON CONFLICT(map_key) DO UPDATE SET
                          canonical_area_id=excluded.canonical_area_id,
                          resolution_method=excluded.resolution_method,
                          overlap_count=excluded.overlap_count,
                          source_buildings=excluded.source_buildings,
                          archive_sha256=excluded.archive_sha256,
                          imported_at=excluded.imported_at""",
                       (key,area_id,str(plan["method"]),int(plan["overlap_count"]),
                        len(buildings),str(batch["archive_sha256"]),now))
        db.execute("UPDATE hk_full_import_batches SET status='applied',resolved_json=? WHERE batch_id=?",
                   (json.dumps(report,ensure_ascii=False,separators=(",",":")),batch_id))
        # The private archive payload is needed only during resolve/apply.
        # Keep the compact resolution report/provenance, but remove staged
        # building rows after a successful import.
        db.execute("DELETE FROM hk_full_import_stage WHERE batch_id=?", (batch_id,))

    unified = cabinet_maps(member)
    return {
        "ok": True,
        "batch_id": batch_id,
        "backup": backup,
        "maps_imported": len(staged),
        "source_buildings_processed": imported_buildings,
        "created_canonical_areas": created_areas,
        "status_counts": report["status_counts"],
        "unified_rows": len(unified.get("maps") or []),
        "source_counts": unified.get("source_counts") or {},
        "area_links": 235,
    }


def _canonical_area_from_exact_buildings(db: sqlite3.Connection, area: dict) -> str:
    """Use exact building IDs to join a live game area to a full-archive canonical area."""
    ids = sorted({str(row.get("building_id") or "") for row in area.get("buildings") or [] if row.get("building_id")})
    if len(ids) < 3:
        return ""
    canonical = _full235_alias_resolver(db)
    counts: dict[str,int] = {}
    # A bounded deterministic sample is enough: building IDs are exact OSM/game IDs.
    sample = ids[:96]
    for start in range(0,len(sample),80):
        chunk = sample[start:start+80]
        sql = "SELECT area_id,building_id FROM map_buildings WHERE building_id IN (%s)" % ",".join("?" for _ in chunk)
        for row in db.execute(sql,tuple(chunk)):
            cid = canonical(str(row["area_id"]))
            counts[cid] = counts.get(cid,0) + 1
    if len(counts) == 1:
        cid,hits = next(iter(counts.items()))
        if hits >= 3:
            return cid
    return ""


''' + anchor
s=s.replace(anchor,insert,1)

# Let current game scans join imported synthetic districts by exact building IDs.
old='''    with db_session() as db:
        canonical_id = canonical_map_area(db, area)
'''
new='''    with db_session() as db:
        overlap_canonical = _canonical_area_from_exact_buildings(db, area) if knowledge_source == "game_live" else ""
        canonical_id = overlap_canonical or canonical_map_area(db, area)
'''
req(old,"submit canonical selection anchor missing")
s=s.replace(old,new,1)

# Add authenticated manager-only cabinet routes before the existing map controls.
route='''            elif path in ("/api/v1/cabinet/maps/publish", "/api/v1/cabinet/maps/member-access", "/api/v1/cabinet/maps/access-scope", "/api/v1/cabinet/maps/open-url"):
'''
req(route,"cabinet maps route anchor missing")
routes=r'''            elif path in ("/api/v1/cabinet/maps/full-import/start",
                             "/api/v1/cabinet/maps/full-import/chunk",
                             "/api/v1/cabinet/maps/full-import/resolve",
                             "/api/v1/cabinet/maps/full-import/apply"):
                origin = self.headers.get("Origin", "")
                if origin not in CABINET_ORIGINS:
                    self.send_cabinet_json(HTTPStatus.FORBIDDEN, {"error":"origin_not_allowed"}); return
                member = self.cabinet_member()
                if not member:
                    self.send_cabinet_json(HTTPStatus.UNAUTHORIZED, {"error":"unauthorized"}); return
                if not member.get("maps_manage"):
                    self.send_cabinet_json(HTTPStatus.FORBIDDEN, {"error":"maps_manage_denied"}); return
                try:
                    maximum = 900_000 if path.endswith("/chunk") else 16_384
                    body = self.read_json(maximum)
                    if path.endswith("/start"):
                        result = full235_import_start(member,body)
                    elif path.endswith("/chunk"):
                        result = full235_import_chunk(member,body)
                    elif path.endswith("/resolve"):
                        result = full235_import_resolve(member,body)
                    else:
                        result = full235_import_apply(member,body)
                    audit("cabinet_full235_"+path.rsplit("/",1)[-1],
                          str(body.get("batch_id","")),self.client_ip(),
                          f"ok={int(bool(result.get('ok')))}")
                    self.send_cabinet_json(HTTPStatus.OK,result)
                except PermissionError:
                    self.send_cabinet_json(HTTPStatus.FORBIDDEN, {"error":"maps_manage_denied"})
                except LookupError:
                    self.send_cabinet_json(HTTPStatus.NOT_FOUND, {"error":"full_import_not_found"})
                except RuntimeError as exc:
                    self.send_cabinet_json(HTTPStatus.CONFLICT, {"error":"full_import_not_ready","detail":str(exc)[:200]})
                except ValueError as exc:
                    self.send_cabinet_json(HTTPStatus.BAD_REQUEST, {"error":"invalid_full_import","detail":str(exc)[:200]})
''' + route
s=s.replace(route,routes,1)

for marker in (
    "HK_FULL235_IMPORT_V1",
    "def full235_import_start",
    "def full235_import_resolve",
    "def full235_import_apply",
    "def _canonical_area_from_exact_buildings",
    "/api/v1/cabinet/maps/full-import/chunk",
):
    req(marker,"missing full235 marker: "+marker)

TARGET.write_text(s,encoding="utf-8")
