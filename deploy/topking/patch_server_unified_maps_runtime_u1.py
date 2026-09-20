from pathlib import Path

TARGET=Path("/tmp/server.py")
s=TARGET.read_text(encoding="utf-8")

def require(x,msg):
    if x not in s:
        raise SystemExit(msg)

# Insert the unified cabinet + legacy website hydration layer immediately before map_index.
anchor='''def map_index() -> list[dict]:
'''
insert=r'''# HK_MAP_UNIFIED_RUNTIME_U1_V1
_cabinet_maps_website_only = cabinet_maps


def _cabinet_unified_canonical_row(row: dict, website: dict | None = None, website_keys: list[str] | None = None) -> dict:
    website = dict(website or {})
    keys = list(website_keys or ([] if not website.get("key") else [str(website["key"])]))
    area_id = str(row.get("area_id") or "")
    x, y = row.get("x"), row.get("y")
    source_kind = "combined" if website else "script"
    synthetic_key = str(website.get("key") or f"canonical:{area_id}")
    crystals = [
        int(row.get("room0") or 0),
        int(row.get("room1") or 0),
        int(row.get("room2") or 0),
        int(row.get("room3") or 0),
        int(row.get("room4") or 0),
        int(row.get("room5") or 0),
    ]
    item = {
        **website,
        "key": synthetic_key,
        "website_key": str(website.get("key") or ""),
        "website_keys": keys,
        "area_id": area_id,
        "canonical_area_id": area_id,
        "source_kind": source_kind,
        "source_label": "Сайт + Скрипт" if source_kind == "combined" else "Скрипт",
        "city": str(row.get("city_name") or row.get("city_id") or website.get("city") or ""),
        "grid": str(website.get("grid") or (f"{x}:{y}" if x is not None and y is not None else "")),
        "canonical_grid": f"{x}:{y}" if x is not None and y is not None else "",
        "x": x,
        "y": y,
        "invest": int(row.get("invest_count") or 0),
        "buildings": int(row.get("buildings") or 0),
        "unknown": int(row.get("unexplored") or 0),
        "crystals": crystals,
        "progress": float(row.get("progress") or 0),
        "score": int(row.get("rating") or 0),
        "shared_known": int(row.get("known") or 0),
        "total_rooms": int(row.get("total_rooms") or 0),
        "open_url": str(website.get("open_url") or ""),
        "published": int(website.get("published") or 0),
        "reward": website.get("reward") or {"max":0,"normal":0,"investment":0},
        "eventBuildings": int(website.get("eventBuildings") or 0),
        "totalEvents": int(website.get("totalEvents") or 0),
        "aliases": list(row.get("aliases") or [area_id]),
    }
    return item


def cabinet_maps(member: dict) -> dict:
    """One Personal Cabinet list: website geometry + canonical/script knowledge."""
    try:
        website = _cabinet_maps_website_only(member)
    except PermissionError:
        website = {"ok": True, "can_manage": bool(member.get("maps_manage")), "maps": [], "members": []}

    website_rows = [dict(row) for row in website.get("maps") or []]
    canonical_rows = map_index()
    canonical_by_id = {str(row.get("area_id") or ""): row for row in canonical_rows}

    with db_session() as db:
        link_rows = db.execute(
            "SELECT map_key,canonical_area_id FROM hk_map_area_links"
        ).fetchall()
        links = {str(row["map_key"]): str(row["canonical_area_id"]) for row in link_rows}
        cities = set()
        map_rules = {}
        if not member.get("maps_manage"):
            cities, map_rules = _hk_member_rules(db, str(member.get("telegram_id") or ""))

    grouped: dict[str, list[dict]] = {}
    unlinked: list[dict] = []
    for row in website_rows:
        key = str(row.get("key") or "")
        area_id = links.get(key, "")
        if area_id and area_id in canonical_by_id:
            grouped.setdefault(area_id, []).append(row)
        else:
            unlinked.append({
                **row,
                "website_key": key,
                "website_keys": [key] if key else [],
                "area_id": "",
                "canonical_area_id": "",
                "source_kind": "website",
                "source_label": "Сайт",
                "canonical_grid": "",
                "shared_known": 0,
                "aliases": [],
            })

    result = []
    used_canonical = set()
    for area_id, rows in grouped.items():
        # If several website visualizations ever point at one canonical district,
        # keep one row and choose the richest website visualization as primary.
        primary = max(
            rows,
            key=lambda row: (
                int(bool(row.get("open_url"))),
                float(row.get("progress") or 0),
                int(row.get("score") or 0),
            ),
        )
        keys = sorted({str(row.get("key") or "") for row in rows if row.get("key")})
        result.append(_cabinet_unified_canonical_row(canonical_by_id[area_id], primary, keys))
        used_canonical.add(area_id)

    result.extend(unlinked)

    for row in canonical_rows:
        area_id = str(row.get("area_id") or "")
        if not area_id or area_id in used_canonical:
            continue
        city = str(row.get("city_name") or row.get("city_id") or "")
        synthetic_key = f"canonical:{area_id}"
        if not member.get("maps_manage"):
            allowed = bool(map_rules.get(synthetic_key, city in cities))
            if not allowed:
                continue
        result.append(_cabinet_unified_canonical_row(row))

    if not result:
        raise PermissionError("maps access denied")

    source_counts = {"website":0,"script":0,"combined":0}
    for row in result:
        kind = str(row.get("source_kind") or "website")
        source_counts[kind] = source_counts.get(kind,0) + 1

    result.sort(key=lambda row: (
        -int(row.get("shared_known") or 0),
        -float(row.get("progress") or 0),
        str(row.get("city") or ""),
        str(row.get("grid") or ""),
    ))
    return {
        "ok": True,
        "can_manage": bool(member.get("maps_manage")),
        "maps": result,
        "members": website.get("members") or [],
        "unified": True,
        "source_counts": source_counts,
        "website_maps": len(website_rows),
        "canonical_maps": len(canonical_rows),
    }


def _hk_parse_geometry_features(value: object) -> list[dict]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return []
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    if isinstance(value, dict) and isinstance(value.get("features"), list):
        return [row for row in value["features"] if isinstance(row, dict)]
    return []


def hydrate_hk_website_map_for_area(canonical_area_id: str, area: dict, geometry: object) -> dict:
    """Safely activate one historical website map when a real game area is scanned.

    Historical website grids are Y:X.  Matching is exact city + canonical X:Y and
    only a single candidate is accepted.  Point links are then derived from the
    game's own building geometry by strict point-in-polygon.
    """
    area_id = str(canonical_area_id or "")
    x, y = area.get("x"), area.get("y")
    city_key = map_city_key(area.get("city_name")) or map_city_key(area.get("city_id"))
    if not area_id or x is None or y is None or not city_key:
        return {"ok": True, "status": "insufficient_area_meta", "matched_maps": 0}

    with db_session() as db:
        catalog = db.execute("SELECT map_key,city,grid FROM hk_maps_catalog ORDER BY map_key").fetchall()
        candidates = []
        for row in catalog:
            match = re.fullmatch(r"\s*(-?\d+)\s*:\s*(-?\d+)\s*", str(row["grid"] or ""))
            if not match:
                continue
            historical_y, historical_x = int(match.group(1)), int(match.group(2))
            row_city = map_city_key(row["city"])
            if row_city == city_key and historical_x == int(x) and historical_y == int(y):
                candidates.append(str(row["map_key"]))
        if len(candidates) != 1:
            return {
                "ok": True,
                "status": "no_unique_website_match" if not candidates else "ambiguous_website_match",
                "matched_maps": len(candidates),
                "map_keys": candidates,
            }
        map_key = candidates[0]
        existing_link = db.execute(
            "SELECT canonical_area_id FROM hk_map_area_links WHERE map_key=?",
            (map_key,),
        ).fetchone()
        if existing_link and str(existing_link["canonical_area_id"]) != area_id:
            return {
                "ok": False,
                "status": "existing_link_conflict",
                "map_key": map_key,
                "canonical_area_id": str(existing_link["canonical_area_id"]),
            }
        point_row = db.execute(
            "SELECT points_json,point_count FROM hk_map_points WHERE map_key=?",
            (map_key,),
        ).fetchone()
        if not point_row:
            return {"ok": True, "status": "website_points_missing", "map_key": map_key}
        try:
            flat = json.loads(point_row["points_json"] or "[]")
        except json.JSONDecodeError:
            flat = []
        canonical_ids = {
            str(row["building_id"])
            for row in db.execute("SELECT building_id FROM map_buildings WHERE area_id=?", (area_id,))
        }
        existing_points = {
            int(row["point_index"]): str(row["building_id"])
            for row in db.execute(
                "SELECT point_index,building_id FROM hk_map_point_links WHERE map_key=?",
                (map_key,),
            )
        }

    # The area relation itself is safe once the unique historical city/grid rule matched.
    if not existing_link:
        link_hk_map_area(map_key, area_id)

    decoded = _hk_upload_decode_points(flat)
    features = {}
    for feature in _hk_parse_geometry_features(geometry):
        props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
        building_id = str(
            props.get("building_id")
            or feature.get("id")
            or props.get("id")
            or props.get("buildingId")
            or ""
        ).strip()
        if building_id not in canonical_ids:
            continue
        if not isinstance(feature.get("geometry"), dict):
            continue
        features[building_id] = feature["geometry"]

    used_buildings = set(existing_points.values())
    links = [{"point_index": index, "building_id": bid} for index,bid in sorted(existing_points.items())]
    unmatched = 0
    ambiguous = 0
    for point in decoded:
        index = int(point["point_index"])
        if index in existing_points:
            continue
        hits = [
            building_id
            for building_id, feature_geometry in features.items()
            if building_id not in used_buildings
            and _hk_upload_geometry_contains(feature_geometry, float(point["lon"]), float(point["lat"]))
        ]
        if len(hits) == 1:
            used_buildings.add(hits[0])
            links.append({"point_index": index, "building_id": hits[0]})
        elif not hits:
            unmatched += 1
        else:
            ambiguous += 1

    if links:
        link_hk_map_points(map_key, links, "exact_building_id")

    by_index = {int(row["point_index"]): str(row["building_id"]) for row in links}
    knowledge = [
        {"building_id": by_index[int(point["point_index"])], "room_count": int(point["room_count"])}
        for point in decoded
        if int(point["point_index"]) in by_index
    ]
    room_result = None
    if knowledge:
        room_result = import_hk_map_room_knowledge(map_key, knowledge)

    return {
        "ok": True,
        "status": "hydrated",
        "map_key": map_key,
        "canonical_area_id": area_id,
        "matched_maps": 1,
        "point_links": len(links),
        "new_point_links": max(0, len(links) - len(existing_points)),
        "unmatched_points": unmatched,
        "ambiguous_points": ambiguous,
        "room_import": room_result,
    }


''' + anchor
require(anchor,"map_index anchor missing")
s=s.replace(anchor,insert,1)

# Hook legacy hydration into the ordinary game-live submit without adding a
# second browser write endpoint.  Geometry is ignored by normalize_map_area.
return_anchor='''    return {"ok":True,"area_id":canonical_id,"source_area_id":area["area_id"],"ignored_complete":False,
            "progress":progress,"buildings":total,"known_buildings":known,"added_buildings":added,"enriched_buildings":enriched}
'''
return_new='''    result = {"ok":True,"area_id":canonical_id,"source_area_id":area["area_id"],"ignored_complete":False,
              "progress":progress,"buildings":total,"known_buildings":known,"added_buildings":added,"enriched_buildings":enriched}
    if knowledge_source == "game_live" and isinstance(value, dict) and value.get("_website_hydrate"):
        try:
            result["website_hydration"] = hydrate_hk_website_map_for_area(
                canonical_id, area, value.get("_website_geometry")
            )
        except Exception as error:
            result["website_hydration"] = {
                "ok": False,
                "status": "hydrate_error",
                "error": str(error)[:240],
            }
    return result
'''
require(return_anchor,"submit return anchor missing")
s=s.replace(return_anchor,return_new,1)

for marker in (
    "HK_MAP_UNIFIED_RUNTIME_U1_V1",
    "_cabinet_maps_website_only = cabinet_maps",
    "def hydrate_hk_website_map_for_area",
    '"source_kind": source_kind',
    'value.get("_website_hydrate")',
):
    require(marker,"missing unified runtime marker: "+marker)

TARGET.write_text(s,encoding="utf-8")
