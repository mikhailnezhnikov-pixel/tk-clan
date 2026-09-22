from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")
MARKER = "CLAN_SHOP_LICENSE_PLAYER_ID_V9"

if MARKER in s:
    print("CLAN_SHOP_LICENSE_PLAYER_ID_V9_ALREADY_PRESENT")
    raise SystemExit(0)

if "CLAN_SHOP_LINKED_PLAYER_ID_V8" not in s:
    raise SystemExit("Clan Shop identity V8 not found")

anchor = "def clan_shop_linked_identities() -> dict[str, dict]:\n"
license_helper = '''def clan_shop_license_identities() -> dict[str, dict]:
    # CLAN_SHOP_LICENSE_PLAYER_ID_V9
    # Canonical identity source: the game player_id entered by the owner when
    # the player is added to HK access / personal cabinet. Display name is the
    # owner's note for that exact ID. No nickname matching is used.
    result = {}
    with db_session() as db:
        rows = db.execute("""
            SELECT player_id,note,active
            FROM licenses
            WHERE player_id IS NOT NULL AND TRIM(player_id)<>''
        """).fetchall()
    for row in rows:
        player_id = str(row["player_id"] or "").strip()
        if not player_id:
            continue
        note = str(row["note"] or "").strip()
        result[player_id] = {
            "player_id": player_id,
            "display_name": note,
            "note": note,
            "active": bool(row["active"]),
        }
    return result


'''
if s.count(anchor) != 1:
    raise SystemExit(f"linked identities anchor expected once, got {s.count(anchor)}")
s = s.replace(anchor, license_helper + anchor, 1)

# Participants: license player_id -> owner note is primary. Telegram-linked
# cabinet identity is only a secondary fallback for older records.
old = '''    linked_identities = clan_shop_linked_identities()
    result = []
'''
new = '''    license_identities = clan_shop_license_identities()
    linked_identities = clan_shop_linked_identities()
    result = []
'''
if s.count(old) < 1:
    raise SystemExit("participants identity maps marker missing")
s = s.replace(old, new, 1)

old = '''        linked = linked_identities.get(player_id) if player_id else None
        nickname = (str(linked.get("display_name") or "").strip() if linked else "") or snapshot_nickname
'''
new = '''        licensed = license_identities.get(player_id) if player_id else None
        linked = linked_identities.get(player_id) if player_id else None
        nickname = (str(licensed.get("display_name") or "").strip() if licensed else "") \
            or (str(linked.get("display_name") or "").strip() if linked else "") \
            or snapshot_nickname
'''
if s.count(old) != 1:
    raise SystemExit(f"participants nickname marker expected once, got {s.count(old)}")
s = s.replace(old, new, 1)

old = '''            "identity_source": "linked_player_id" if linked else "clan_snapshot",
'''
new = '''            "identity_source": "license_player_id" if licensed and licensed.get("display_name") else (
                "linked_player_id" if linked and linked.get("display_name") else "clan_snapshot"
            ),
'''
if s.count(old) != 1:
    raise SystemExit(f"participants identity_source marker expected once, got {s.count(old)}")
s = s.replace(old, new, 1)

# History: load both direct-ID registries, with licenses first.
old = '''    linked_identities = clan_shop_linked_identities()

    # The actual-purchase collector is authenticated by the real game player ID.
'''
new = '''    license_identities = clan_shop_license_identities()
    linked_identities = clan_shop_linked_identities()

    # The actual-purchase collector is authenticated by the real game player ID.
'''
if s.count(old) != 1:
    raise SystemExit(f"history identity maps marker expected once, got {s.count(old)}")
s = s.replace(old, new, 1)

old = '''            participant = by_player_id.get(pid)
            linked = linked_identities.get(pid)
            nickname = (
                str(linked.get("display_name") or "").strip()
                if linked else ""
            ) or (
                str(participant.get("nickname") or "").strip()
                if participant else ""
            ) or full_snapshot_nickname_by_player_id.get(pid, "") \
              or latest_nickname_by_player_id.get(pid, "") \
              or pid
            player_key = "id:" + pid
'''
new = '''            participant = by_player_id.get(pid)
            licensed = license_identities.get(pid)
            linked = linked_identities.get(pid)
            nickname = (
                str(licensed.get("display_name") or "").strip()
                if licensed else ""
            ) or (
                str(linked.get("display_name") or "").strip()
                if linked else ""
            ) or (
                str(participant.get("nickname") or "").strip()
                if participant else ""
            ) or full_snapshot_nickname_by_player_id.get(pid, "") \
              or latest_nickname_by_player_id.get(pid, "") \
              or pid
            player_key = "id:" + pid
'''
if s.count(old) != 1:
    raise SystemExit(f"history nickname marker expected once, got {s.count(old)}")
s = s.replace(old, new, 1)

old = '''                "identity_source": "linked_player_id" if linked else (
                    "clan_snapshot" if participant or pid in full_snapshot_nickname_by_player_id
                    else ("skill_snapshot" if pid in latest_nickname_by_player_id else "player_id")
                ),
'''
new = '''                "identity_source": "license_player_id" if licensed and licensed.get("display_name") else (
                    "linked_player_id" if linked and linked.get("display_name") else (
                        "clan_snapshot" if participant or pid in full_snapshot_nickname_by_player_id
                        else ("skill_snapshot" if pid in latest_nickname_by_player_id else "player_id")
                    )
                ),
'''
if s.count(old) != 1:
    raise SystemExit(f"history identity_source marker expected once, got {s.count(old)}")
s = s.replace(old, new, 1)

path.write_text(s, encoding="utf-8")
print("CLAN_SHOP_LICENSE_PLAYER_ID_V9_PATCH_OK")
