from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")
MARKER = "CLAN_SHOP_CABINET_LINKED_ID_V12"

if MARKER in s:
    print(MARKER + "_ALREADY_PRESENT")
    raise SystemExit(0)

if "CLAN_SHOP_LICENSE_PLAYER_ID_V11" not in s:
    raise SystemExit("Clan Shop V11 marker missing")

# Canon:
# - identity key is the exact game player_id;
# - a cabinet member is linked only by clan_members.linked_player_id;
# - if linked, display the label from that cabinet member record;
# - if not linked, fall back to game snapshots / numeric player_id;
# - never infer a link from nickname and never use the separate licenses registry
#   to rename an unlinked Clan Shop player.

# Add an explicit marker near the canonical linked identity helper.
anchor = "def clan_shop_linked_identities() -> dict[str, dict]:\n"
if anchor not in s:
    raise SystemExit("linked identity helper missing")
s = s.replace(
    anchor,
    "# " + MARKER + "\n" + anchor,
    1,
)

# Participants: V11 inserted the license registry before linked identities.
old = '''    license_identities = clan_shop_license_identities()
    linked_identities = clan_shop_linked_identities()
    result = []
'''
new = '''    linked_identities = clan_shop_linked_identities()
    result = []
'''
if old not in s:
    raise SystemExit("participants V11 identity prelude missing")
s = s.replace(old, new, 1)

old = '''        licensed = license_identities.get(player_id) if player_id else None
        linked = linked_identities.get(player_id) if player_id else None
        nickname = (str(licensed.get("display_name") or "").strip() if licensed else "") \
            or (str(linked.get("display_name") or "").strip() if linked else "") \
            or snapshot_nickname
'''
new = '''        linked = linked_identities.get(player_id) if player_id else None
        nickname = (str(linked.get("display_name") or "").strip() if linked else "") \
            or snapshot_nickname
'''
if old not in s:
    raise SystemExit("participants V11 nickname block missing")
s = s.replace(old, new, 1)

old = '''            "identity_source": "license_player_id" if licensed and licensed.get("display_name") else (
                "linked_player_id" if linked and linked.get("display_name") else "clan_snapshot"
            ),
'''
new = '''            "identity_source": "linked_player_id" if linked and linked.get("display_name") else "clan_snapshot",
'''
if old not in s:
    raise SystemExit("participants V11 identity source missing")
s = s.replace(old, new, 1)

# History: exact player_id row is preserved even when no cabinet member exists.
# Only clan_members.linked_player_id may supply a cabinet display name.
old = '''    license_identities=clan_shop_license_identities()
    linked_identities=clan_shop_linked_identities()

    latest_nickname_by_player_id={}
'''
new = '''    linked_identities=clan_shop_linked_identities()

    latest_nickname_by_player_id={}
'''
if old not in s:
    raise SystemExit("history V11 identity prelude missing")
s = s.replace(old, new, 1)

old = '''        participant=by_player_id.get(pid)
        licensed=license_identities.get(pid)
        linked=linked_identities.get(pid)
        nickname=(
            str(licensed.get("display_name") or "").strip() if licensed else ""
        ) or (
            str(linked.get("display_name") or "").strip() if linked else ""
        ) or (
'''
new = '''        participant=by_player_id.get(pid)
        linked=linked_identities.get(pid)
        nickname=(
            str(linked.get("display_name") or "").strip() if linked else ""
        ) or (
'''
if old not in s:
    raise SystemExit("history V11 nickname prefix missing")
s = s.replace(old, new, 1)

old = '''            "identity_source":"license_player_id" if licensed and licensed.get("display_name") else (
                "linked_player_id" if linked and linked.get("display_name") else (
                    "clan_snapshot" if participant or pid in full_snapshot_nickname_by_player_id
                    else ("skill_snapshot" if pid in latest_nickname_by_player_id else "player_id")
                )
            ),
'''
new = '''            "identity_source":"linked_player_id" if linked and linked.get("display_name") else (
                "clan_snapshot" if participant or pid in full_snapshot_nickname_by_player_id
                else ("skill_snapshot" if pid in latest_nickname_by_player_id else "player_id")
            ),
'''
if old not in s:
    raise SystemExit("history V11 identity source missing")
s = s.replace(old, new, 1)

# V10 already keeps the clan-shared remainder in coverage.pending only.
# Guard against regressions that turn that remainder into a fake player row.
history_start = s.index("def clan_shop_history_payload() -> dict:")
history_end = s.index("\ndef clan_shop_publication_text", history_start)
history = s[history_start:history_end]
for forbidden in [
    '"nickname": "Не распределено по игрокам"',
    '"nickname": "Не определён игрок"',
    '"player_key": "unknown:',
    '"player_key": "unattributed:',
]:
    if forbidden in history:
        raise SystemExit("fake unattributed player row still present: " + forbidden)

path.write_text(s, encoding="utf-8")
print("CLAN_SHOP_CABINET_LINKED_ID_V12_PATCH_OK")
