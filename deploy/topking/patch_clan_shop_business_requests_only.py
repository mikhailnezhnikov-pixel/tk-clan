from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text()
MARKER = "CLAN_SHOP_BUSINESS_REQUESTS_ONLY_V3"
if MARKER in s:
    print("CLAN_SHOP_BUSINESS_REQUESTS_ONLY_ALREADY_PRESENT")
    raise SystemExit(0)

# Mark the feature and force player requests to business only.
needle = '''def set_clan_shop_request(member: dict, body: dict) -> dict:
    ensure_clan_shop_schema()
'''
replacement = '''# CLAN_SHOP_BUSINESS_REQUESTS_ONLY_V3
def set_clan_shop_request(member: dict, body: dict) -> dict:
    ensure_clan_shop_schema()
'''
if needle not in s:
    raise SystemExit("request function anchor missing")
s = s.replace(needle, replacement, 1)

old_parse = '''    try:
        idol_orbs = int(body.get("idol_orbs") or 0)
        businesses = int(body.get("splus_businesses") or 0)
    except (TypeError, ValueError):
        raise ValueError("invalid quantity")
    if not (0 <= idol_orbs <= CLAN_SHOP_PER_PLAYER_LIMIT
            and 0 <= businesses <= CLAN_SHOP_PER_PLAYER_LIMIT):
        raise ValueError("invalid quantity")
'''
new_parse = '''    try:
        businesses = int(body.get("splus_businesses") or 0)
    except (TypeError, ValueError):
        raise ValueError("invalid quantity")
    idol_orbs = 0
    if not (0 <= businesses <= CLAN_SHOP_PER_PLAYER_LIMIT):
        raise ValueError("invalid quantity")
'''
if old_parse not in s:
    raise SystemExit("request quantity block missing")
s = s.replace(old_parse, new_parse, 1)

# Old pending idol requests should no longer appear as player requests.
old_payload = '''        item["request_idol_orbs"] = int(request["idol_orbs"] or 0) if request else 0
        item["request_splus_businesses"] = int(request["splus_businesses"] or 0) if request else 0
'''
new_payload = '''        item["request_idol_orbs"] = 0
        item["request_splus_businesses"] = int(request["splus_businesses"] or 0) if request else 0
'''
if old_payload not in s:
    raise SystemExit("request payload block missing")
s = s.replace(old_payload, new_payload, 1)

# A manager may accept only S+ business requests.
old_items = '''    if item not in ("idol_orbs", "splus_businesses"):
        raise ValueError("invalid item")
'''
new_items = '''    if item != "splus_businesses":
        raise ValueError("invalid item")
'''
if old_items not in s:
    raise SystemExit("accept item block missing")
s = s.replace(old_items, new_items, 1)

# Zero any stale idol request amounts when a member updates their request.
# This also converts previously saved dual-item requests to business-only.
path.write_text(s)
print("CLAN_SHOP_BUSINESS_REQUESTS_ONLY_PATCH_OK")
