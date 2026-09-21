from pathlib import Path

TARGET = Path("/tmp/server.py")
s = TARGET.read_text(encoding="utf-8")

def req(value: str, message: str) -> None:
    if value not in s:
        raise SystemExit(message)

MARKER = "# HK_MAP_VISIBILITY_ACCESS_V2\n"
if MARKER in s:
    print("HK_MAP_VISIBILITY_ACCESS_V2_ALREADY_PRESENT")
    raise SystemExit(0)

req("# HK_MAP_UNIFIED_RUNTIME_U1_V1\n", "unified maps U1 marker missing")
req("def member_can_access_hk_map(", "scoped map access helper missing")
req("def map_index() -> list[dict]:\n", "map_index anchor missing")
req('if not public and not member_can_access_hk_map(member, map_key, row["city"]):', "private map data gate missing")

insert = r'''# HK_MAP_VISIBILITY_ACCESS_V2
# All authenticated cabinet members may see the unified map catalogue.
# Opening private map data remains protected by member_can_access_hk_map().
_cabinet_maps_access_filtered_u1 = cabinet_maps


def cabinet_maps(member: dict) -> dict:
    actual_manager = bool(member.get("maps_manage"))

    # U1 already knows how to construct the complete, deduplicated catalogue.
    # Ask it for the manager view only to avoid filtering rows out of the list;
    # do not expose manager permissions/members to an ordinary viewer.
    if actual_manager:
        result = _cabinet_maps_access_filtered_u1(member)
    else:
        catalogue_member = dict(member)
        catalogue_member["maps_manage"] = 1
        catalogue_member["maps_access"] = 1
        result = _cabinet_maps_access_filtered_u1(catalogue_member)

    maps = [dict(row) for row in result.get("maps") or []]

    if actual_manager:
        for row in maps:
            website_key = str(row.get("website_key") or "")
            if not website_key and str(row.get("key") or "").startswith("hk_"):
                website_key = str(row.get("key") or "")
            has_map = bool(website_key and row.get("open_url"))
            row["access_allowed"] = bool(has_map)
            row["access_state"] = "granted" if has_map else "unavailable"
            row["access_key"] = website_key
    else:
        telegram_id = str(member.get("telegram_id") or "")
        ensure_scoped_hk_map_access_schema()
        with db_session() as db:
            cities, map_rules = _hk_member_rules(db, telegram_id)

        for row in maps:
            website_key = str(row.get("website_key") or "")
            if not website_key and str(row.get("key") or "").startswith("hk_"):
                website_key = str(row.get("key") or "")
            has_map = bool(website_key and row.get("open_url"))
            if has_map:
                city = str(row.get("city") or "")
                allowed = bool(map_rules.get(website_key, city in cities))
            else:
                allowed = False
            row["access_allowed"] = allowed
            row["access_state"] = "granted" if allowed else ("locked" if has_map else "unavailable")
            row["access_key"] = website_key

    result = dict(result)
    result["maps"] = maps
    result["can_manage"] = actual_manager
    result["members"] = result.get("members") or [] if actual_manager else []
    result["catalogue_visible_to_all_members"] = True
    result["private_map_access_enforced"] = True
    return result


''' + "def map_index() -> list[dict]:\n"

s = s.replace("def map_index() -> list[dict]:\n", insert, 1)

for check in (
    "HK_MAP_VISIBILITY_ACCESS_V2",
    "_cabinet_maps_access_filtered_u1 = cabinet_maps",
    'result["catalogue_visible_to_all_members"] = True',
    'result["private_map_access_enforced"] = True',
    '"access_state"'
):
    req(check, "missing visibility access v2 marker: " + check)

TARGET.write_text(s, encoding="utf-8")
print("HK_MAP_VISIBILITY_ACCESS_V2_PATCH=PASS")
