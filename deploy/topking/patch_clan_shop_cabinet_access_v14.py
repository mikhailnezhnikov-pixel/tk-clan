from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")
MARKER = "CLAN_SHOP_CABINET_ACCESS_V14"

if MARKER in s:
    print(MARKER + "_ALREADY_PRESENT")
    raise SystemExit(0)

if "CLAN_SHOP_KNOWN_PLAYER_ID_FALLBACK_V13" not in s:
    raise SystemExit("Clan Shop V13 marker missing")

# Cabinet identity canon:
# - purchases are keyed ONLY by exact game player_id;
# - active records in the cabinet access registry (licenses) define who is a
#   cabinet user and supply the owner-defined display name;
# - clan_members.linked_player_id is optional metadata/fallback, not a required
#   condition for being a cabinet user;
# - nickname text is never used as a join key.

anchor = "def clan_shop_linked_identities() -> dict[str, dict]:\n"
helper = '''def clan_shop_cabinet_access_identities() -> dict[str, dict]:
    # CLAN_SHOP_CABINET_ACCESS_V14
    # The access registry is canonical for cabinet membership. Exact player_id
    # is the only join key.
    result = {}
    for player_id, row in clan_shop_license_identities().items():
        if not row.get("active"):
            continue
        display_name = str(row.get("display_name") or "").strip()
        result[str(player_id)] = {
            **row,
            "player_id": str(player_id),
            "display_name": display_name,
            "cabinet_access": True,
        }
    return result


'''
if anchor not in s:
    raise SystemExit("linked identity anchor missing")
s = s.replace(anchor, helper + anchor, 1)

# Current Clan Shop participant list: access registry name first.
old = '''    linked_identities = clan_shop_linked_identities()
    result = []
'''
new = '''    access_identities = clan_shop_cabinet_access_identities()
    linked_identities = clan_shop_linked_identities()
    result = []
'''
if old not in s:
    raise SystemExit("participants identity prelude missing")
s = s.replace(old, new, 1)

old = '''        linked = linked_identities.get(player_id) if player_id else None
        nickname = (str(linked.get("display_name") or "").strip() if linked else "") \
            or snapshot_nickname
'''
new = '''        access = access_identities.get(player_id) if player_id else None
        linked = linked_identities.get(player_id) if player_id else None
        nickname = (str(access.get("display_name") or "").strip() if access else "") \
            or (str(linked.get("display_name") or "").strip() if linked else "") \
            or snapshot_nickname
'''
if old not in s:
    raise SystemExit("participants nickname block missing")
s = s.replace(old, new, 1)

old = '''            "identity_source": "linked_player_id" if linked and linked.get("display_name") else "clan_snapshot",
'''
new = '''            "identity_source": "cabinet_access" if access else (
                "linked_player_id" if linked and linked.get("display_name") else "clan_snapshot"
            ),
            "cabinet_access": bool(access),
'''
if old not in s:
    raise SystemExit("participants identity source missing")
s = s.replace(old, new, 1)

# History: cabinet access record is primary identity for the same exact player_id.
history_start = s.index("def clan_shop_history_payload() -> dict:")
history_end = s.index("\ndef clan_shop_publication_text", history_start)
history = s[history_start:history_end]

old = '''    linked_identities=clan_shop_linked_identities()
    known_player_identities=clan_shop_license_identities()  # exact player_id fallback only

    latest_nickname_by_player_id={}
'''
new = '''    access_identities=clan_shop_cabinet_access_identities()
    linked_identities=clan_shop_linked_identities()
    known_player_identities=clan_shop_license_identities()  # inactive/historical exact-ID fallback only

    latest_nickname_by_player_id={}
'''
if old not in history:
    raise SystemExit("history identity prelude missing")
history = history.replace(old, new, 1)

old = '''        participant=by_player_id.get(pid)
        linked=linked_identities.get(pid)
        known=known_player_identities.get(pid)
        nickname=(
            str(linked.get("display_name") or "").strip() if linked else ""
        ) or (
'''
new = '''        participant=by_player_id.get(pid)
        access=access_identities.get(pid)
        linked=linked_identities.get(pid)
        known=known_player_identities.get(pid)
        nickname=(
            str(access.get("display_name") or "").strip() if access else ""
        ) or (
            str(linked.get("display_name") or "").strip() if linked else ""
        ) or (
'''
if old not in history:
    raise SystemExit("history nickname prefix missing")
history = history.replace(old, new, 1)

old = '''            "identity_source":"linked_player_id" if linked and linked.get("display_name") else (
                "clan_snapshot" if participant or pid in full_snapshot_nickname_by_player_id else (
                    "skill_snapshot" if pid in latest_nickname_by_player_id else (
                        "known_player_id" if known and known.get("display_name") else "player_id"
                    )
                )
            ),
            "cabinet_linked":bool(linked),
'''
new = '''            "identity_source":"cabinet_access" if access else (
                "linked_player_id" if linked and linked.get("display_name") else (
                    "clan_snapshot" if participant or pid in full_snapshot_nickname_by_player_id else (
                        "skill_snapshot" if pid in latest_nickname_by_player_id else (
                            "known_player_id" if known and known.get("display_name") else "player_id"
                        )
                    )
                )
            ),
            "cabinet_access":bool(access),
            "cabinet_linked":bool(linked),
'''
if old not in history:
    raise SystemExit("history identity source block missing")
history = history.replace(old, new, 1)

# Weekly aggregation must stay keyed by (week_start, exact player_id).
for required in [
    'key=(week,"id:"+pid)',
    '"week_start":week',
    '"player_id":pid',
]:
    if required not in history:
        raise SystemExit("weekly exact-id history invariant missing: " + required)

for forbidden in [
    '"nickname": "Не распределено по игрокам"',
    '"nickname": "Не определён игрок"',
    '"player_key": "unknown:',
    '"player_key": "unattributed:',
]:
    if forbidden in history:
        raise SystemExit("fake unattributed player row present: " + forbidden)

s = s[:history_start] + history + s[history_end:]
path.write_text(s, encoding="utf-8")
print("CLAN_SHOP_CABINET_ACCESS_V14_PATCH_OK")
