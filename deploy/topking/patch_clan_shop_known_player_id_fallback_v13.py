from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")
MARKER = "CLAN_SHOP_KNOWN_PLAYER_ID_FALLBACK_V13"

if MARKER in s:
    print(MARKER + "_ALREADY_PRESENT")
    raise SystemExit(0)

if "CLAN_SHOP_CABINET_LINKED_ID_V12" not in s:
    raise SystemExit("Clan Shop V12 marker missing")

# Canon:
# 1. Row identity is always the exact game player_id.
# 2. Cabinet linkage is ONLY clan_members.linked_player_id.
# 3. For an unlinked player we may still display a known name, but only when
#    that name is attached to the exact same player_id in a trusted game/history
#    source. This never turns the player into a linked cabinet member.
# 4. Nickname text is never used as a join key.

history_start = s.index("def clan_shop_history_payload() -> dict:")
history_end = s.index("\\ndef clan_shop_publication_text", history_start)
history = s[history_start:history_end]

old = '''    linked_identities=clan_shop_linked_identities()

    latest_nickname_by_player_id={}
'''
new = '''    linked_identities=clan_shop_linked_identities()
    known_player_identities=clan_shop_license_identities()  # exact player_id fallback only

    latest_nickname_by_player_id={}
'''
if old not in history:
    raise SystemExit("history identity prelude missing")
history = history.replace(old, new, 1)

old = '''        participant=by_player_id.get(pid)
        linked=linked_identities.get(pid)
        nickname=(
'''
new = '''        participant=by_player_id.get(pid)
        linked=linked_identities.get(pid)
        known=known_player_identities.get(pid)
        nickname=(
'''
if old not in history:
    raise SystemExit("history player identity prefix missing")
history = history.replace(old, new, 1)

old = '''          or latest_nickname_by_player_id.get(pid,"") \\
          or pid
'''
new = '''          or latest_nickname_by_player_id.get(pid,"") \\
          or (str(known.get("display_name") or "").strip() if known else "") \\
          or pid
'''
if old not in history:
    raise SystemExit("history fallback tail missing")
history = history.replace(old, new, 1)

old = '''            "identity_source":"linked_player_id" if linked and linked.get("display_name") else (
                "clan_snapshot" if participant or pid in full_snapshot_nickname_by_player_id
                else ("skill_snapshot" if pid in latest_nickname_by_player_id else "player_id")
            ),
'''
new = '''            "identity_source":"linked_player_id" if linked and linked.get("display_name") else (
                "clan_snapshot" if participant or pid in full_snapshot_nickname_by_player_id else (
                    "skill_snapshot" if pid in latest_nickname_by_player_id else (
                        "known_player_id" if known and known.get("display_name") else "player_id"
                    )
                )
            ),
            "cabinet_linked":bool(linked),
'''
if old not in history:
    raise SystemExit("history identity_source block missing")
history = history.replace(old, new, 1)

# Exact-ID fallback must not create fake unattributed player rows.
for forbidden in [
    '"nickname": "Не распределено по игрокам"',
    '"nickname": "Не определён игрок"',
    '"player_key": "unknown:',
    '"player_key": "unattributed:',
]:
    if forbidden in history:
        raise SystemExit("fake unattributed player row present: " + forbidden)

s = s[:history_start] + history + s[history_end:]
# Leave a visible server marker outside the function as well.
s = s.replace(
    "# CLAN_SHOP_CABINET_LINKED_ID_V12\\ndef clan_shop_linked_identities()",
    "# CLAN_SHOP_CABINET_LINKED_ID_V12\\n# " + MARKER + "\\ndef clan_shop_linked_identities()",
    1,
)

path.write_text(s, encoding="utf-8")
print("CLAN_SHOP_KNOWN_PLAYER_ID_FALLBACK_V13_PATCH_OK")
