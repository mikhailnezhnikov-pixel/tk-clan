from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")
MARKER = "CLAN_SHOP_IDENTITY_RESOLUTION_V7"

if MARKER in s:
    print("CLAN_SHOP_IDENTITY_RESOLUTION_V7_ALREADY_PRESENT")
    raise SystemExit(0)

if "CLAN_SHOP_IDENTITY_RESOLUTION_V6" not in s:
    raise SystemExit("V6 identity function not found")

needle = '''    latest_nickname_by_player_id = {}
    with db_session() as db:
        try:
            nickname_rows = db.execute("""
                SELECT s.player_id,s.nickname
                FROM clan_skill_snapshots AS s
                JOIN (
                    SELECT player_id,MAX(scanned_at) AS scanned_at
                    FROM clan_skill_snapshots
                    WHERE nickname<>''
                    GROUP BY player_id
                ) AS latest
                  ON latest.player_id=s.player_id AND latest.scanned_at=s.scanned_at
                WHERE s.nickname<>''
            """).fetchall()
            for row in nickname_rows:
                pid = str(row["player_id"] or "").strip()
                nickname = str(row["nickname"] or "").strip()
                if pid and nickname:
                    latest_nickname_by_player_id[pid] = nickname
        except sqlite3.Error:
            pass

        lots = db.execute("""SELECT week_start,lot_id,item_type,lot_name,reward_id,
'''

replacement = '''    # CLAN_SHOP_IDENTITY_RESOLUTION_V7
    latest_nickname_by_player_id = {}
    full_snapshot_nickname_by_player_id = {}
    with db_session() as db:
        try:
            nickname_rows = db.execute("""
                SELECT s.player_id,s.nickname
                FROM clan_skill_snapshots AS s
                JOIN (
                    SELECT player_id,MAX(scanned_at) AS scanned_at
                    FROM clan_skill_snapshots
                    WHERE nickname<>''
                    GROUP BY player_id
                ) AS latest
                  ON latest.player_id=s.player_id AND latest.scanned_at=s.scanned_at
                WHERE s.nickname<>''
            """).fetchall()
            for row in nickname_rows:
                pid = str(row["player_id"] or "").strip()
                nickname = str(row["nickname"] or "").strip()
                if pid and nickname:
                    latest_nickname_by_player_id[pid] = nickname
        except sqlite3.Error:
            pass

        try:
            snapshot_rows = db.execute("""
                SELECT snapshot_json,captured_at
                FROM clan_skill_full_snapshots
                ORDER BY captured_at DESC
                LIMIT 24
            """).fetchall()
            for snapshot_row in snapshot_rows:
                try:
                    document_value = json.loads(snapshot_row["snapshot_json"] or "{}")
                except (json.JSONDecodeError, TypeError):
                    continue
                stack = [document_value]
                while stack:
                    value = stack.pop()
                    if isinstance(value, dict):
                        pid = str(value.get("player_id") or value.get("playerId") or "").strip()
                        nickname = str(value.get("nickname") or value.get("name") or "").strip()
                        if pid and nickname and pid not in full_snapshot_nickname_by_player_id:
                            full_snapshot_nickname_by_player_id[pid] = nickname
                        stack.extend(value.values())
                    elif isinstance(value, list):
                        stack.extend(value)
        except sqlite3.Error:
            pass

        lots = db.execute("""SELECT week_start,lot_id,item_type,lot_name,reward_id,
'''

if s.count(needle) != 1:
    raise SystemExit(f"V6 name map block: expected 1 match, got {s.count(needle)}")
s = s.replace(needle, replacement, 1)

old_name = '''            nickname = (
                str(participant.get("nickname") or "").strip()
                if participant else latest_nickname_by_player_id.get(pid, "")
            ) or pid
'''

new_name = '''            nickname = (
                str(participant.get("nickname") or "").strip()
                if participant else ""
            ) or full_snapshot_nickname_by_player_id.get(pid, "") \
              or latest_nickname_by_player_id.get(pid, "") \
              or pid
'''

if s.count(old_name) != 1:
    raise SystemExit(f"V6 nickname selection: expected 1 match, got {s.count(old_name)}")
s = s.replace(old_name, new_name, 1)

path.write_text(s, encoding="utf-8")
print("CLAN_SHOP_IDENTITY_RESOLUTION_V7_PATCH_OK")
