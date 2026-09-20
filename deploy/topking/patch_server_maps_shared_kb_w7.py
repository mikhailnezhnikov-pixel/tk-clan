from pathlib import Path

TARGET=Path("/tmp/server.py")
s=TARGET.read_text(encoding="utf-8")

def require(x,msg):
    if x not in s:
        raise SystemExit(msg)

anchor='''    return {"ok": True, "received": len(rows), "accepted": accepted, "points": total_points}


'''
insert=anchor+'''# HK_MAP_AUTHORIZED_UPLOAD_W7_V1
def _hk_upload_decode_points(flat: list[int]) -> list[dict]:
    lng = lat = 0
    rows = []
    for offset in range(0, len(flat), 3):
        lng += int(flat[offset])
        lat += int(flat[offset + 1])
        flag = int(flat[offset + 2])
        rows.append({
            "point_index": offset // 3,
            "lon": lng / 100000.0,
            "lat": lat / 100000.0,
            "room_count": flag & 0x07,
            "is_invest": bool(flag & 0x08),
            "source_flag": flag,
        })
    return rows


def _hk_upload_ring_contains(ring: object, x: float, y: float) -> bool:
    if not isinstance(ring, list) or len(ring) < 3:
        return False
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        a, b = ring[i], ring[j]
        if not (isinstance(a, list) and isinstance(b, list) and len(a) >= 2 and len(b) >= 2):
            j = i
            continue
        xi, yi = float(a[0]), float(a[1])
        xj, yj = float(b[0]), float(b[1])
        if (yi > y) != (yj > y):
            cross = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < cross:
                inside = not inside
        j = i
    return inside


def _hk_upload_geometry_contains(geometry: object, x: float, y: float) -> bool:
    if not isinstance(geometry, dict):
        return False
    kind = geometry.get("type")
    coords = geometry.get("coordinates")
    polygons = []
    if kind == "Polygon" and isinstance(coords, list):
        polygons = [coords]
    elif kind == "MultiPolygon" and isinstance(coords, list):
        polygons = coords
    else:
        return False
    for polygon in polygons:
        if not isinstance(polygon, list) or not polygon:
            continue
        if not _hk_upload_ring_contains(polygon[0], x, y):
            continue
        if any(_hk_upload_ring_contains(hole, x, y) for hole in polygon[1:]):
            continue
        return True
    return False


def import_hk_authorized_map_upload(value: object) -> dict:
    """Direct website upload -> canonical shared map knowledge.

    Required upload contract:
      catalog: existing HK Maps index row (contains key/city/grid)
      points: compact delta point array
      meta: explicit canonical coordinates + coord_revision
      buildingsGeoJSON: authorized full source with building_id properties

    No login/session/cookie data is stored.
    """
    if not isinstance(value, dict):
        raise ValueError("invalid authorized map upload")
    catalog = value.get("catalog")
    meta = value.get("meta")
    collection = value.get("buildingsGeoJSON")
    flat = value.get("points")
    if not isinstance(catalog, dict) or not isinstance(meta, dict):
        raise ValueError("missing catalog/meta")
    features = collection.get("features") if isinstance(collection, dict) else None
    if not isinstance(features, list):
        raise ValueError("missing buildings GeoJSON")
    key = str(catalog.get("key") or "").strip()
    if not re.fullmatch(r"hk_[a-z0-9]+", key):
        raise ValueError("invalid map key")
    if not isinstance(flat, list) or len(flat) % 3 or len(flat) > 300000:
        raise ValueError("invalid map points")
    clean = []
    for item in flat:
        if isinstance(item, bool) or not isinstance(item, int):
            raise ValueError("invalid map point value")
        clean.append(int(item))

    revision = str(meta.get("coord_revision") or "").strip()
    try:
        mx, my = int(meta.get("x")), int(meta.get("y"))
    except (TypeError, ValueError):
        raise ValueError("invalid canonical coordinates")
    if revision in ("column-row-v1", "canonical-xy"):
        canonical_x, canonical_y = mx, my
    elif revision == "historical-yx":
        canonical_x, canonical_y = my, mx
    else:
        raise ValueError("explicit coord_revision required")

    area_id = str(meta.get("area_id") or "").strip()
    city_id = str(meta.get("city_id") or "").strip()
    city_name = str(meta.get("city_name") or catalog.get("city") or "").strip()
    if not ID_RE.fullmatch(area_id) or not ID_RE.fullmatch(city_id) or not city_name:
        raise ValueError("invalid canonical map metadata")

    game_features = {}
    area_buildings = []
    for feature in features:
        props = feature.get("properties") if isinstance(feature, dict) else None
        if not isinstance(props, dict) or not props.get("is_game"):
            continue
        building_id = str(props.get("building_id") or feature.get("id") or "").strip()
        if not ID_RE.fullmatch(building_id) or building_id in game_features:
            continue
        crystals = props.get("crystals")
        try:
            room_count = None if crystals is None else max(0, min(20, int(crystals)))
        except (TypeError, ValueError):
            room_count = None
        row = {
            "building_id": building_id,
            "opened": room_count is not None,
            "room_count": room_count,
            "has_events": room_count is not None and room_count > 0,
            "is_invest": bool(props.get("is_investment")),
            "tier": None,
            "faction": str(props.get("faction") or "")[:40],
            "building_type": str(props.get("building_generator") or "")[:100],
        }
        area_buildings.append(row)
        game_features[building_id] = {
            "row": row,
            "geometry": feature.get("geometry"),
        }
    if not area_buildings:
        raise ValueError("authorized upload has no game buildings")

    decoded = _hk_upload_decode_points(clean)
    explicit_links = value.get("point_links")
    point_links = []
    unmatched = []
    ambiguous = []
    if isinstance(explicit_links, list):
        seen_points = set()
        seen_buildings = set()
        for raw in explicit_links:
            if not isinstance(raw, dict):
                continue
            try:
                point_index = int(raw.get("point_index"))
            except (TypeError, ValueError):
                continue
            building_id = str(raw.get("building_id") or "").strip()
            if not 0 <= point_index < len(decoded):
                continue
            if building_id not in game_features or point_index in seen_points or building_id in seen_buildings:
                continue
            seen_points.add(point_index)
            seen_buildings.add(building_id)
            point_links.append({"point_index": point_index, "building_id": building_id})
    else:
        used = set()
        for point in decoded:
            candidates = []
            for building_id, item in game_features.items():
                if building_id in used:
                    continue
                if not _hk_upload_geometry_contains(item["geometry"], point["lon"], point["lat"]):
                    continue
                feature_room = item["row"]["room_count"]
                if feature_room is not None and int(feature_room) != int(point["room_count"]):
                    continue
                candidates.append(building_id)
            if len(candidates) == 1:
                building_id = candidates[0]
                used.add(building_id)
                point_links.append({"point_index": point["point_index"], "building_id": building_id})
            elif not candidates:
                unmatched.append(point["point_index"])
            else:
                ambiguous.append({"point_index": point["point_index"], "building_ids": sorted(candidates)})

    link_by_index = {row["point_index"]: row["building_id"] for row in point_links}
    room_knowledge = []
    for point in decoded:
        building_id = link_by_index.get(point["point_index"])
        if building_id:
            room_knowledge.append({"building_id": building_id, "room_count": point["room_count"]})

    area = {
        "area_id": area_id,
        "city_id": city_id,
        "city_name": city_name,
        "x": canonical_x,
        "y": canonical_y,
        "invest_count": int(catalog.get("invest") or sum(1 for row in area_buildings if row["is_invest"])),
        "expected_buildings": int(catalog.get("buildings") or len(area_buildings)),
        "buildings": area_buildings,
    }

    # All input is validated before any write. The remaining operations are
    # idempotent, so a retry after infrastructure failure is safe.
    canonical = submit_map_area("source-hk-maps-import", area)
    canonical_id = str(canonical["area_id"])
    index_result = import_hk_maps_index([catalog])
    points_result = import_hk_map_points([[key, clean]])
    area_link = link_hk_map_area(key, canonical_id)
    point_result = None
    room_result = None
    if point_links:
        point_result = link_hk_map_points(key, point_links, "exact_building_id")
        room_result = import_hk_map_room_knowledge(key, room_knowledge)

    detail = map_detail(canonical_id)
    return {
        "ok": True,
        "map_key": key,
        "canonical_area_id": canonical_id,
        "coord_revision": revision,
        "direct_shared": True,
        "sync_required": False,
        "catalog": index_result,
        "points": points_result,
        "canonical": canonical,
        "area_link": area_link["link"],
        "point_links": 0 if point_result is None else point_result["total"],
        "matched_points": len(point_links),
        "unmatched_points": unmatched,
        "ambiguous_points": ambiguous,
        "room_import": room_result,
        "shared_buildings": 0 if not detail else len(detail["buildings"]),
    }


'''
require(anchor,"import_hk_map_points return anchor missing")
s=s.replace(anchor,insert,1)

cli_anchor='''    elif "--import-hk-map-points" in os.sys.argv:
        if len(os.sys.argv) < 3:
            raise SystemExit("usage: server.py --import-hk-map-points FILE.json.gz")
        init_db()
        with gzip.open(os.sys.argv[2], "rt", encoding="utf-8") as source:
            print(json.dumps(import_hk_map_points(json.load(source))))
'''
cli_new=cli_anchor+'''    elif "--import-hk-authorized-map" in os.sys.argv:
        if len(os.sys.argv) < 3:
            raise SystemExit("usage: server.py --import-hk-authorized-map FILE.json[.gz]")
        init_db()
        opener = gzip.open if os.sys.argv[2].endswith(".gz") else open
        with opener(os.sys.argv[2], "rt", encoding="utf-8") as source:
            print(json.dumps(import_hk_authorized_map_upload(json.load(source))))
'''
require(cli_anchor,"authorized upload CLI anchor missing")
s=s.replace(cli_anchor,cli_new,1)

for marker in (
    "HK_MAP_AUTHORIZED_UPLOAD_W7_V1",
    "def import_hk_authorized_map_upload",
    '"sync_required": False',
    'elif "--import-hk-authorized-map" in os.sys.argv:',
):
    require(marker,"missing W7 marker: "+marker)

TARGET.write_text(s,encoding="utf-8")
