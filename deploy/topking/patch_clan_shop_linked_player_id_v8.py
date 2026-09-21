from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")
MARKER = "CLAN_SHOP_LINKED_PLAYER_ID_V8"

if MARKER in s:
    print("CLAN_SHOP_LINKED_PLAYER_ID_V8_ALREADY_PRESENT")
    raise SystemExit(0)

if "CLAN_SHOP_IDENTITY_RESOLUTION_V7" not in s:
    raise SystemExit("Clan Shop identity V7 not found")

# Add one canonical helper: linked_player_id is the primary identity source.
anchor = "def clan_shop_participants() -> list[dict]:\n"
helper = '''def clan_shop_linked_identities() -> dict[str, dict]:
    # CLAN_SHOP_LINKED_PLAYER_ID_V8
    result = {}
    with db_session() as db:
        rows = db.execute("""
            SELECT linked_player_id,note,first_name,username,active
            FROM clan_members
            WHERE linked_player_id IS NOT NULL AND TRIM(linked_player_id)<>''
        """).fetchall()
    for row in rows:
        player_id = str(row["linked_player_id"] or "").strip()
        if not player_id:
            continue
        note = str(row["note"] or "").strip()
        first_name = str(row["first_name"] or "").strip()
        username = str(row["username"] or "").strip()
        display_name = note or first_name or (("@" + username) if username else "")
        result[player_id] = {
            "player_id": player_id,
            "display_name": display_name,
            "note": note,
            "first_name": first_name,
            "username": username,
            "active": bool(row["active"]),
        }
    return result


'''
if s.count(anchor) != 1:
    raise SystemExit(f"participants anchor expected once, got {s.count(anchor)}")
s = s.replace(anchor, helper + anchor, 1)

# Current Clan Shop participant list must use the cabinet label whenever the
# player is linked by game ID. Nickname matching is never used for identity.
old_participants = '''def clan_shop_participants() -> list[dict]:
    full = latest_clan_full_snapshot()
    overall = full.get("overall") if isinstance(full, dict) and isinstance(full.get("overall"), list) else []
    result = []
    seen = set()
    for row in overall:
        if not isinstance(row, dict):
            continue
        player_id = str(row.get("player_id") or "").strip()
        nickname = str(row.get("nickname") or "").strip()[:100]
        if not nickname:
            continue
        if player_id:
            player_key = "id:" + player_id
        else:
            player_key = "nick:" + hashlib.sha256(nickname.encode("utf-8")).hexdigest()[:24]
        if player_key in seen:
            continue
        seen.add(player_key)
        result.append({"player_key": player_key, "player_id": player_id, "nickname": nickname})
    result.sort(key=lambda item: item["nickname"].casefold())
    return result
'''

new_participants = '''def clan_shop_participants() -> list[dict]:
    full = latest_clan_full_snapshot()
    overall = full.get("overall") if isinstance(full, dict) and isinstance(full.get("overall"), list) else []
    linked_identities = clan_shop_linked_identities()
    result = []
    seen = set()
    for row in overall:
        if not isinstance(row, dict):
            continue
        player_id = str(row.get("player_id") or "").strip()
        snapshot_nickname = str(row.get("nickname") or "").strip()[:100]
        linked = linked_identities.get(player_id) if player_id else None
        nickname = (str(linked.get("display_name") or "").strip() if linked else "") or snapshot_nickname
        if not nickname:
            continue
        if player_id:
            player_key = "id:" + player_id
        else:
            player_key = "nick:" + hashlib.sha256(nickname.encode("utf-8")).hexdigest()[:24]
        if player_key in seen:
            continue
        seen.add(player_key)
        result.append({
            "player_key": player_key,
            "player_id": player_id,
            "nickname": nickname,
            "identity_source": "linked_player_id" if linked else "clan_snapshot",
        })
    result.sort(key=lambda item: item["nickname"].casefold())
    return result
'''
if s.count(old_participants) != 1:
    raise SystemExit(f"old participants function expected once, got {s.count(old_participants)}")
s = s.replace(old_participants, new_participants, 1)

# History: resolve direct cabinet link first, then clan snapshot, then skill
# snapshot, and only lastly the numeric ID.
needle = '''    participants = clan_shop_participants()
    by_player_id = {
        str(row.get("player_id") or ""): row
        for row in participants if row.get("player_id")
    }

    # The actual-purchase collector is authenticated by the real game player ID.
'''
replacement = '''    participants = clan_shop_participants()
    by_player_id = {
        str(row.get("player_id") or ""): row
        for row in participants if row.get("player_id")
    }
    linked_identities = clan_shop_linked_identities()

    # The actual-purchase collector is authenticated by the real game player ID.
'''
if s.count(needle) != 1:
    raise SystemExit(f"history identity prelude expected once, got {s.count(needle)}")
s = s.replace(needle, replacement, 1)

old_name = '''            participant = by_player_id.get(pid)
            nickname = (
                str(participant.get("nickname") or "").strip()
                if participant else ""
            ) or full_snapshot_nickname_by_player_id.get(pid, "") \
              or latest_nickname_by_player_id.get(pid, "") \
              or pid
            player_key = (
                str(participant.get("player_key") or ("id:" + pid))
                if participant else ("id:" + pid)
            )
'''
new_name = '''            participant = by_player_id.get(pid)
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
if s.count(old_name) != 1:
    raise SystemExit(f"history nickname block expected once, got {s.count(old_name)}")
s = s.replace(old_name, new_name, 1)

# Record source for UI/debugging without changing existing consumers.
old_item = '''                "nickname": nickname,
                "idol_orbs": 0,
'''
new_item = '''                "nickname": nickname,
                "identity_source": "linked_player_id" if linked else (
                    "clan_snapshot" if participant or pid in full_snapshot_nickname_by_player_id
                    else ("skill_snapshot" if pid in latest_nickname_by_player_id else "player_id")
                ),
                "idol_orbs": 0,
'''
if s.count(old_item) < 1:
    raise SystemExit("history item nickname marker missing")
s = s.replace(old_item, new_item, 1)

path.write_text(s, encoding="utf-8")
print("CLAN_SHOP_LINKED_PLAYER_ID_V8_PATCH_OK")
