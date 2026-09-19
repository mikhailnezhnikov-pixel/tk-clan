from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text()
MARKER = "CLAN_SHOP_ACTUAL_FACTS_V5"
if MARKER in s:
    print("CLAN_SHOP_ACTUAL_FACTS_ALREADY_PRESENT")
    raise SystemExit(0)

# Extend Clan Shop schema with actual in-game facts.
old_schema = '''            CREATE TABLE IF NOT EXISTS clan_shop_requests (
                week_start TEXT NOT NULL,
                player_key TEXT NOT NULL,
                player_id TEXT NOT NULL DEFAULT '',
                nickname TEXT NOT NULL,
                idol_orbs INTEGER NOT NULL DEFAULT 0,
                splus_businesses INTEGER NOT NULL DEFAULT 0,
                updated_by TEXT NOT NULL DEFAULT '',
                updated_at INTEGER NOT NULL,
                PRIMARY KEY (week_start, player_key)
            );
            CREATE INDEX IF NOT EXISTS idx_clan_shop_requests_week
                ON clan_shop_requests(week_start, updated_at);
'''
new_schema = '''            CREATE TABLE IF NOT EXISTS clan_shop_requests (
                week_start TEXT NOT NULL,
                player_key TEXT NOT NULL,
                player_id TEXT NOT NULL DEFAULT '',
                nickname TEXT NOT NULL,
                idol_orbs INTEGER NOT NULL DEFAULT 0,
                splus_businesses INTEGER NOT NULL DEFAULT 0,
                updated_by TEXT NOT NULL DEFAULT '',
                updated_at INTEGER NOT NULL,
                PRIMARY KEY (week_start, player_key)
            );
            CREATE INDEX IF NOT EXISTS idx_clan_shop_requests_week
                ON clan_shop_requests(week_start, updated_at);
            CREATE TABLE IF NOT EXISTS clan_shop_actual_lots (
                week_start TEXT NOT NULL,
                lot_id TEXT NOT NULL,
                item_type TEXT NOT NULL,
                lot_name TEXT NOT NULL DEFAULT '',
                reward_id TEXT NOT NULL DEFAULT '',
                shared_purchased INTEGER NOT NULL DEFAULT 0,
                shared_maximum INTEGER NOT NULL DEFAULT 0,
                updated_at INTEGER NOT NULL,
                PRIMARY KEY (week_start, lot_id)
            );
            CREATE INDEX IF NOT EXISTS idx_clan_shop_actual_lots_week
                ON clan_shop_actual_lots(week_start, item_type, updated_at);
            CREATE TABLE IF NOT EXISTS clan_shop_actual_players (
                week_start TEXT NOT NULL,
                lot_id TEXT NOT NULL,
                item_type TEXT NOT NULL,
                player_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                updated_at INTEGER NOT NULL,
                PRIMARY KEY (week_start, lot_id, player_id)
            );
            CREATE INDEX IF NOT EXISTS idx_clan_shop_actual_players_week
                ON clan_shop_actual_players(week_start, item_type, player_id);
'''
if old_schema not in s:
    raise SystemExit("clan shop requests schema anchor missing")
s = s.replace(old_schema, new_schema, 1)

anchor = '\ndef clan_shop_history_payload() -> dict:\n'
functions = r'''
# CLAN_SHOP_ACTUAL_FACTS_V5
def clan_shop_actual_week(now_ts: int | None = None) -> dict:
    import datetime as _dt
    tz = _dt.timezone(_dt.timedelta(hours=3))
    now_value = int(now_ts if now_ts is not None else utc_now())
    local_now = _dt.datetime.fromtimestamp(now_value, _dt.timezone.utc).astimezone(tz)
    monday = local_now.date() - _dt.timedelta(days=local_now.weekday())
    sunday = monday + _dt.timedelta(days=6)
    return {
        "week_start": monday.isoformat(),
        "week_end": sunday.isoformat(),
        "week_label": f"{monday.strftime('%d.%m')}–{sunday.strftime('%d.%m.%Y')}",
    }


def submit_clan_shop_actual_facts(player_id: str, rows: object) -> dict:
    ensure_clan_shop_schema()
    if not isinstance(rows, list):
        raise ValueError("rows array required")
    rows = rows[:20]
    week_start = clan_shop_actual_week()["week_start"]
    now = utc_now()
    accepted = 0
    with db_session() as db:
        for raw in rows:
            if not isinstance(raw, dict):
                continue
            lot_id = str(raw.get("lot_id") or "").strip()[:160]
            item_type = str(raw.get("item_type") or "").strip()
            if not lot_id or item_type not in ("idol_orbs", "splus_businesses"):
                continue
            lot_name = str(raw.get("lot_name") or "").strip()[:300]
            reward_id = str(raw.get("reward_id") or "").strip()[:160]
            try:
                shared_purchased = max(0, min(10000, int(raw.get("shared_purchased") or 0)))
                shared_maximum = max(0, min(10000, int(raw.get("shared_maximum") or 0)))
                player_purchased = max(0, min(10000, int(raw.get("player_purchased") or 0)))
            except (TypeError, ValueError):
                continue
            if shared_maximum and shared_purchased > shared_maximum:
                shared_purchased = shared_maximum

            db.execute("""INSERT INTO clan_shop_actual_lots(
                            week_start,lot_id,item_type,lot_name,reward_id,
                            shared_purchased,shared_maximum,updated_at)
                          VALUES(?,?,?,?,?,?,?,?)
                          ON CONFLICT(week_start,lot_id) DO UPDATE SET
                            item_type=excluded.item_type,
                            lot_name=CASE WHEN excluded.lot_name<>'' THEN excluded.lot_name ELSE clan_shop_actual_lots.lot_name END,
                            reward_id=CASE WHEN excluded.reward_id<>'' THEN excluded.reward_id ELSE clan_shop_actual_lots.reward_id END,
                            shared_purchased=MAX(clan_shop_actual_lots.shared_purchased,excluded.shared_purchased),
                            shared_maximum=MAX(clan_shop_actual_lots.shared_maximum,excluded.shared_maximum),
                            updated_at=excluded.updated_at""",
                       (week_start, lot_id, item_type, lot_name, reward_id,
                        shared_purchased, shared_maximum, now))

            db.execute("""INSERT INTO clan_shop_actual_players(
                            week_start,lot_id,item_type,player_id,quantity,updated_at)
                          VALUES(?,?,?,?,?,?)
                          ON CONFLICT(week_start,lot_id,player_id) DO UPDATE SET
                            item_type=excluded.item_type,
                            quantity=MAX(clan_shop_actual_players.quantity,excluded.quantity),
                            updated_at=excluded.updated_at""",
                       (week_start, lot_id, item_type, str(player_id), player_purchased, now))
            accepted += 1
    return {"ok": True, "week_start": week_start, "accepted": accepted}


def clan_shop_history_payload() -> dict:
    ensure_clan_shop_schema()
    participants = clan_shop_participants()
    by_player_id = {str(row.get("player_id") or ""): row for row in participants if row.get("player_id")}
    with db_session() as db:
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
            nickname = str(participant.get("nickname") or "") if participant else pid
            player_key = str(participant.get("player_key") or ("id:" + pid)) if participant else ("id:" + pid)
            key = (week, player_key)
            item = aggregated.setdefault(key, {
                "week_start": week,
                "player_key": player_key,
                "player_id": pid,
                "nickname": nickname,
                "idol_orbs": 0,
                "splus_businesses": 0,
                "recorded_at": 0,
            })
            item[item_type] += quantity
            item["recorded_at"] = max(item["recorded_at"], int(row["updated_at"] or 0))

        shared_total = max(0, int(lot["shared_purchased"] or 0))
        actual_total = max(shared_total, known_total)
        unknown = max(0, actual_total - known_total)
        if unknown > 0:
            key = (week, item_type)
            unknown_by_week[key] = unknown_by_week.get(key, 0) + unknown

    for (week, item_type), quantity in unknown_by_week.items():
        key = (week, "unknown")
        item = aggregated.setdefault(key, {
            "week_start": week,
            "player_key": "unknown:" + week,
            "player_id": "",
            "nickname": "Не определён игрок",
            "idol_orbs": 0,
            "splus_businesses": 0,
            "recorded_at": 0,
        })
        item[item_type] += int(quantity)

    items = list(aggregated.values())
    items.sort(key=lambda row: (row["week_start"], row["nickname"].casefold()), reverse=True)
    return {"ok": True, "source": "game_actual", "items": items}


'''
if anchor not in s:
    raise SystemExit("clan shop history payload anchor missing")

# Replace the old history function entirely through the next function definition.
start = s.index(anchor) + 1
next_anchor = '\ndef clan_shop_publication_text(payload: dict) -> str:\n'
end = s.index(next_anchor, start)
s = s[:start] + functions + s[end:]

# Add authenticated game script endpoint before settings routes.
post_anchor = '''            elif path in ("/api/v1/settings/load", "/api/v1/settings/save"):
'''
post_route = '''            elif path == "/api/v1/clan-shop-facts/submit":
                origin = self.headers.get("Origin", "")
                if origin not in ALLOWED_ORIGINS:
                    self.send_json(HTTPStatus.FORBIDDEN, {"error": "origin_not_allowed"})
                    return
                player_id = self.recipe_player()
                if not player_id:
                    self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                    return
                try:
                    body = self.read_json(100_000)
                    result = submit_clan_shop_actual_facts(player_id, body.get("rows"))
                    self.send_json(HTTPStatus.OK, result)
                except ValueError:
                    self.send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_clan_shop_facts"})
            elif path in ("/api/v1/settings/load", "/api/v1/settings/save"):
'''
if post_anchor not in s:
    raise SystemExit("settings route anchor missing")
s = s.replace(post_anchor, post_route, 1)

path.write_text(s)
print("CLAN_SHOP_ACTUAL_FACTS_PATCH_OK")
