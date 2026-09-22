from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text(encoding="utf-8")
MARKER="CLAN_SHOP_CURRENT_ROSTER_ONLY_V19"

if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)
if "CLAN_SHOP_ACCESS_PARTICIPANTS_V15" not in s:
    raise SystemExit("Clan Shop V15 marker missing")

start=s.index("def clan_shop_participants() -> list[dict]:")
end=s.index("\ndef ",start+1)
block=s[start:end]

old='''    # CLAN_SHOP_ACCESS_PARTICIPANTS_V15
    # Active cabinet access is sufficient to appear in the admin Clan Shop
    # allocation list. A current clan snapshot can enrich the row, but is not
    # required. Exact player_id remains the only identity key.
    for player_id, access in access_identities.items():
        player_id=str(player_id or "").strip()
        if not player_id:
            continue
        player_key="id:"+player_id
        if player_key in seen:
            continue
        seen.add(player_key)
        display_name=str(access.get("display_name") or "").strip() or player_id
        result.append({
            "player_key":player_key,
            "player_id":player_id,
            "nickname":display_name,
            "identity_source":"cabinet_access",
            "cabinet_access":True,
        })

    result.sort(key=lambda item: item["nickname"].casefold())
'''
new='''    # CLAN_SHOP_CURRENT_ROSTER_ONLY_V19
    # The allocation list is the CURRENT in-game clan roster only.
    # Cabinet-access records enrich roster members by the same exact player_id
    # but are never appended as extra participants. This prevents the historic
    # access registry from doubling the roster.
    result.sort(key=lambda item: item["nickname"].casefold())
'''
if old not in block:
    raise SystemExit("V15 access append block missing")
block=block.replace(old,new,1)

# Legacy snapshots used the opaque member.id instead of numeric player_id.
# Do not claim "без ЛК" for those rows because exact access status is unknown
# until a corrected snapshot arrives.
old2='''            "cabinet_access": bool(access),
'''
new2='''            "cabinet_access": (bool(access) if player_id.isdigit() else None),
'''
if old2 not in block:
    raise SystemExit("cabinet_access row missing")
block=block.replace(old2,new2,1)

s=s[:start]+block+s[end:]
path.write_text(s,encoding="utf-8")
print("CLAN_SHOP_CURRENT_ROSTER_ONLY_V19_PATCH_OK")
