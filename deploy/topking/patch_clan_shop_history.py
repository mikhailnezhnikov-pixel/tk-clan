from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text()
MARKER = "CLAN_SHOP_HISTORY_V4"
if MARKER in s:
    print("CLAN_SHOP_HISTORY_ALREADY_PRESENT")
    raise SystemExit(0)

# Extend schema with published allocation snapshots.
old_schema = '''            CREATE TABLE IF NOT EXISTS clan_shop_publications (
                week_start TEXT PRIMARY KEY,
                published_at INTEGER NOT NULL,
                published_by TEXT NOT NULL DEFAULT '',
                message_text TEXT NOT NULL DEFAULT ''
            );
'''
new_schema = '''            CREATE TABLE IF NOT EXISTS clan_shop_publications (
                week_start TEXT PRIMARY KEY,
                published_at INTEGER NOT NULL,
                published_by TEXT NOT NULL DEFAULT '',
                message_text TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS clan_shop_publication_items (
                week_start TEXT NOT NULL,
                player_key TEXT NOT NULL,
                player_id TEXT NOT NULL DEFAULT '',
                nickname TEXT NOT NULL,
                idol_orbs INTEGER NOT NULL DEFAULT 0,
                splus_businesses INTEGER NOT NULL DEFAULT 0,
                published_at INTEGER NOT NULL,
                PRIMARY KEY (week_start, player_key)
            );
            CREATE INDEX IF NOT EXISTS idx_clan_shop_publication_items_week
                ON clan_shop_publication_items(week_start, published_at);
'''
if old_schema not in s:
    raise SystemExit("publication schema anchor missing")
s = s.replace(old_schema, new_schema, 1)

# Add history builder before publication text.
anchor = '\ndef clan_shop_publication_text(payload: dict) -> str:\n'
history_fn = r'''
# CLAN_SHOP_HISTORY_V4
def clan_shop_history_payload() -> dict:
    ensure_clan_shop_schema()
    with db_session() as db:
        rows = db.execute("""SELECT week_start,player_key,player_id,nickname,
                                    idol_orbs,splus_businesses,published_at
                             FROM clan_shop_publication_items
                             ORDER BY week_start DESC,nickname COLLATE NOCASE""").fetchall()
    items = []
    for row in rows:
        items.append({
            "week_start": str(row["week_start"]),
            "player_key": str(row["player_key"]),
            "player_id": str(row["player_id"] or ""),
            "nickname": str(row["nickname"] or ""),
            "idol_orbs": int(row["idol_orbs"] or 0),
            "splus_businesses": int(row["splus_businesses"] or 0),
            "published_at": int(row["published_at"] or 0),
        })
    return {"ok": True, "items": items}


'''
if anchor not in s:
    raise SystemExit("history function anchor missing")
s = s.replace(anchor, '\n' + history_fn + 'def clan_shop_publication_text(payload: dict) -> str:\n', 1)

# Replace publication DB write with snapshot persistence.
old_publish_db = '''    ensure_clan_shop_schema()
    with db_session() as db:
        db.execute("""INSERT INTO clan_shop_publications(
                        week_start,published_at,published_by,message_text)
                      VALUES(?,?,?,?)
                      ON CONFLICT(week_start) DO UPDATE SET
                        published_at=excluded.published_at,
                        published_by=excluded.published_by,
                        message_text=excluded.message_text""",
                   (payload["window"]["week_start"], utc_now(),
                    str(member.get("telegram_id") or ""), text))
    result = clan_shop_payload(member)
'''
new_publish_db = '''    ensure_clan_shop_schema()
    published_at = utc_now()
    week_start = payload["window"]["week_start"]
    with db_session() as db:
        db.execute("""INSERT INTO clan_shop_publications(
                        week_start,published_at,published_by,message_text)
                      VALUES(?,?,?,?)
                      ON CONFLICT(week_start) DO UPDATE SET
                        published_at=excluded.published_at,
                        published_by=excluded.published_by,
                        message_text=excluded.message_text""",
                   (week_start, published_at,
                    str(member.get("telegram_id") or ""), text))
        db.execute("DELETE FROM clan_shop_publication_items WHERE week_start=?", (week_start,))
        for row in payload.get("participants") or []:
            idols = int(row.get("idol_orbs") or 0)
            businesses = int(row.get("splus_businesses") or 0)
            if idols <= 0 and businesses <= 0:
                continue
            db.execute("""INSERT INTO clan_shop_publication_items(
                            week_start,player_key,player_id,nickname,
                            idol_orbs,splus_businesses,published_at)
                          VALUES(?,?,?,?,?,?,?)""",
                       (week_start, str(row.get("player_key") or ""),
                        str(row.get("player_id") or ""), str(row.get("nickname") or ""),
                        idols, businesses, published_at))
    result = clan_shop_payload(member)
'''
if old_publish_db not in s:
    raise SystemExit("publish DB block missing")
s = s.replace(old_publish_db, new_publish_db, 1)

# Add GET history route before main clan-shop route.
get_anchor = '''        elif path == "/api/v1/cabinet/clan-shop":
            origin = self.headers.get("Origin", "")
'''
get_route = '''        elif path == "/api/v1/cabinet/clan-shop/history":
            origin = self.headers.get("Origin", "")
            if origin not in CABINET_ORIGINS:
                self.send_cabinet_json(HTTPStatus.FORBIDDEN, {"error": "origin_not_allowed"})
                return
            member = self.cabinet_member()
            if not member:
                self.send_cabinet_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            self.send_cabinet_json(HTTPStatus.OK, clan_shop_history_payload())
        elif path == "/api/v1/cabinet/clan-shop":
            origin = self.headers.get("Origin", "")
'''
if get_anchor not in s:
    raise SystemExit("clan shop GET anchor missing")
s = s.replace(get_anchor, get_route, 1)

path.write_text(s)
print("CLAN_SHOP_HISTORY_PATCH_OK")
