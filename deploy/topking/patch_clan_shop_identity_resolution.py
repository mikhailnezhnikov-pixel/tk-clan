from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")
MARKER = "CLAN_SHOP_IDENTITY_RESOLUTION_V6"
if MARKER in s:
    print("CLAN_SHOP_IDENTITY_RESOLUTION_ALREADY_PRESENT")
    raise SystemExit(0)

start_marker = "def clan_shop_history_payload() -> dict:\n"
end_marker = "\ndef clan_shop_publication_text(payload: dict) -> str:\n"
if start_marker not in s or end_marker not in s:
    raise SystemExit("clan shop history function anchors missing")

start = s.index(start_marker)
end = s.index(end_marker, start)
old = s[start:end]

required = [
    "participants = clan_shop_participants()",
    "by_player_id = {str(row.get(\"player_id\") or \"\"): row for row in participants if row.get(\"player_id\")}",
    "nickname = str(participant.get(\"nickname\") or \"\") if participant else pid",
    "\"nickname\": \"Не определён игрок\"",
]
for marker in required:
    if marker not in old:
        raise SystemExit("expected history marker missing: " + marker)

new = r'''def clan_shop_history_payload() -> dict:
    # CLAN_SHOP_IDENTITY_RESOLUTION_V6
    ensure_clan_shop_schema()
    participants = clan_shop_participants()
    by_player_id = {
        str(row.get("player_id") or ""): row
        for row in participants if row.get("player_id")
    }

    # The actual-purchase collector is authenticated by the real game player ID.
    # A current clan snapshot can temporarily omit IDs for some members, so use
    # the player's latest own clan-skill submission as a stable nickname fallback.
    latest_nickname_by_player_id = {}
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
                                    shared_purchased,shared_maximum,updated_at
                             FROM clan_shop_actual_lots
                             ORDER BY week_start DESC,lot_id""").fetchall()
        player_rows = db.execute("""SELECT week_start,lot_id,item_type,player_id,quantity,updated_at
                                    FROM clan_shop_actual_players
                                    ORDER BY week_start DESC,lot_id,player_id""").fetchall()

    players_by_lot = {}
    for row in player_rows:
        key = (str(row["week_start"]), str(row["lot_id"]))
        players_by_lot.setdefault(key, []).append(row)

    aggregated = {}
    unknown_by_week = {}
    for lot in lots:
        week = str(lot["week_start"])
        item_type = str(lot["item_type"])
        lot_id = str(lot["lot_id"])
        known_total = 0
        for row in players_by_lot.get((week, lot_id), []):
            quantity = max(0, int(row["quantity"] or 0))
            if quantity <= 0:
                continue
            known_total += quantity
            pid = str(row["player_id"])
            participant = by_player_id.get(pid)
            nickname = (
                str(participant.get("nickname") or "").strip()
                if participant else latest_nickname_by_player_id.get(pid, "")
            ) or pid
            player_key = (
                str(participant.get("player_key") or ("id:" + pid))
                if participant else ("id:" + pid)
            )
            key = (week, player_key)
            item = aggregated.setdefault(key, {
                "week_start": week,
                "player_key": player_key,
                "player_id": pid,
                "nickname": nickname,
                "idol_orbs": 0,
                "splus_businesses": 0,
                "recorded_at": 0,
                "is_unattributed": False,
            })
            item[item_type] += quantity
            item["recorded_at"] = max(item["recorded_at"], int(row["updated_at"] or 0))

        shared_total = max(0, int(lot["shared_purchased"] or 0))
        actual_total = max(shared_total, known_total)
        unknown = max(0, actual_total - known_total)
        if unknown > 0:
            key = (week, item_type)
            unknown_by_week[key] = unknown_by_week.get(key, 0) + unknown

    # This remainder is not one mysterious player. It is the shared-shop total
    # that cannot yet be attributed because those buyers have not submitted
    # their personal purchase counters. Represent it as an unattributed bucket.
    for (week, item_type), quantity in unknown_by_week.items():
        key = (week, "unattributed")
        item = aggregated.setdefault(key, {
            "week_start": week,
            "player_key": "unattributed:" + week,
            "player_id": "",
            "nickname": "Не распределено по игрокам",
            "idol_orbs": 0,
            "splus_businesses": 0,
            "recorded_at": 0,
            "is_unattributed": True,
        })
        item[item_type] += int(quantity)

    items = list(aggregated.values())
    items.sort(key=lambda row: (
        row["week_start"],
        bool(row.get("is_unattributed")),
        row["nickname"].casefold(),
    ), reverse=True)
    return {"ok": True, "source": "game_actual", "items": items}

'''

s = s[:start] + new + s[end:]
path.write_text(s, encoding="utf-8")
print("CLAN_SHOP_IDENTITY_RESOLUTION_V6_PATCH_OK")
