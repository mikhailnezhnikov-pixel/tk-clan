from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text(encoding="utf-8")
MARKER="CLAN_SHOP_PURCHASE_EVENTS_V16"

if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)
if "CLAN_SHOP_ACCESS_PARTICIPANTS_V15" not in s:
    raise SystemExit("Clan Shop V15 marker missing")

# Add an independent event schema. These are authoritative rows from the
# in-game clan purchase history, keyed by exact buyer player_id.
anchor="def clan_shop_history_payload() -> dict:\n"
helper=r'''def ensure_clan_shop_purchase_event_schema() -> None:
    # CLAN_SHOP_PURCHASE_EVENTS_V16
    with db_session() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS clan_shop_purchase_events (
            event_key TEXT PRIMARY KEY,
            purchased_at INTEGER NOT NULL,
            week_start TEXT NOT NULL,
            buyer_player_id TEXT NOT NULL DEFAULT '',
            buyer_nickname TEXT NOT NULL DEFAULT '',
            lot_id TEXT NOT NULL DEFAULT '',
            item_type TEXT NOT NULL,
            lot_name TEXT NOT NULL DEFAULT '',
            source_path TEXT NOT NULL DEFAULT '',
            captured_by TEXT NOT NULL DEFAULT '',
            captured_at INTEGER NOT NULL
        )""")
        db.execute("""CREATE INDEX IF NOT EXISTS idx_clan_shop_purchase_events_week
                      ON clan_shop_purchase_events(week_start,item_type,buyer_player_id)""")


def _clan_shop_purchase_event_ts(value) -> int:
    import datetime as _dt
    if value is None or value == "":
        return 0
    if isinstance(value,(int,float)):
        number=float(value)
        if number > 10_000_000_000:
            number/=1000.0
        return max(0,int(number))
    text=str(value).strip()
    if not text:
        return 0
    try:
        number=float(text)
        if number > 10_000_000_000:
            number/=1000.0
        return max(0,int(number))
    except ValueError:
        pass
    try:
        parsed=_dt.datetime.fromisoformat(text.replace("Z","+00:00"))
        if parsed.tzinfo is None:
            parsed=parsed.replace(tzinfo=_dt.timezone.utc)
        return max(0,int(parsed.timestamp()))
    except ValueError:
        return 0


def submit_clan_shop_purchase_events(collector_player_id: str, rows: object) -> dict:
    ensure_clan_shop_schema()
    ensure_clan_shop_purchase_event_schema()
    if not isinstance(rows,list):
        raise ValueError("rows array required")
    now=utc_now()
    accepted=0
    unresolved=0
    with db_session() as db:
        for raw in rows[:500]:
            if not isinstance(raw,dict):
                continue
            event_key=str(raw.get("event_key") or "").strip()[:240]
            item_type=str(raw.get("item_type") or "").strip()
            if not event_key or item_type not in ("idol_orbs","splus_businesses"):
                continue
            purchased_at=_clan_shop_purchase_event_ts(raw.get("purchased_at"))
            if purchased_at <= 0:
                continue
            buyer_player_id=str(raw.get("buyer_player_id") or "").strip()[:80]
            if buyer_player_id and not buyer_player_id.isdigit():
                continue
            buyer_nickname=str(raw.get("buyer_nickname") or "").strip()[:160]
            lot_id=str(raw.get("lot_id") or "").strip()[:180]
            lot_name=str(raw.get("lot_name") or "").strip()[:320]
            source_path=str(raw.get("source_path") or "").strip()[:240]
            week_start=clan_shop_actual_week(purchased_at)["week_start"]
            db.execute("""INSERT INTO clan_shop_purchase_events(
                            event_key,purchased_at,week_start,buyer_player_id,buyer_nickname,
                            lot_id,item_type,lot_name,source_path,captured_by,captured_at)
                          VALUES(?,?,?,?,?,?,?,?,?,?,?)
                          ON CONFLICT(event_key) DO UPDATE SET
                            purchased_at=excluded.purchased_at,
                            week_start=excluded.week_start,
                            buyer_player_id=CASE WHEN excluded.buyer_player_id<>'' THEN excluded.buyer_player_id ELSE clan_shop_purchase_events.buyer_player_id END,
                            buyer_nickname=CASE WHEN excluded.buyer_nickname<>'' THEN excluded.buyer_nickname ELSE clan_shop_purchase_events.buyer_nickname END,
                            lot_id=CASE WHEN excluded.lot_id<>'' THEN excluded.lot_id ELSE clan_shop_purchase_events.lot_id END,
                            item_type=excluded.item_type,
                            lot_name=CASE WHEN excluded.lot_name<>'' THEN excluded.lot_name ELSE clan_shop_purchase_events.lot_name END,
                            source_path=CASE WHEN excluded.source_path<>'' THEN excluded.source_path ELSE clan_shop_purchase_events.source_path END,
                            captured_by=excluded.captured_by,
                            captured_at=excluded.captured_at""",
                       (event_key,purchased_at,week_start,buyer_player_id,buyer_nickname,
                        lot_id,item_type,lot_name,source_path,str(collector_player_id or ""),now))
            accepted+=1
            if not buyer_player_id:
                unresolved+=1
    return {"ok":True,"accepted":accepted,"unresolved":unresolved}


'''
if anchor not in s:
    raise SystemExit("history anchor missing")
s=s.replace(anchor,helper+anchor,1)

# Extend history payload with authoritative event rows. For each
# week/player/item we use the larger of the personal counter and the number of
# distinct purchase-history events. This avoids double-counting while allowing
# a partially captured history page to improve coverage immediately.
old='''        player_rows=db.execute("""SELECT week_start,lot_id,item_type,player_id,quantity,updated_at
                                  FROM clan_shop_actual_players
                                  ORDER BY week_start DESC,lot_id,player_id""").fetchall()

    shared_by_week={}
'''
new='''        player_rows=db.execute("""SELECT week_start,lot_id,item_type,player_id,quantity,updated_at
                                  FROM clan_shop_actual_players
                                  ORDER BY week_start DESC,lot_id,player_id""").fetchall()
        ensure_clan_shop_purchase_event_schema()
        event_rows=db.execute("""SELECT week_start,item_type,buyer_player_id AS player_id,
                                        COUNT(*) AS quantity,MAX(captured_at) AS updated_at
                                 FROM clan_shop_purchase_events
                                 WHERE buyer_player_id<>''
                                 GROUP BY week_start,item_type,buyer_player_id
                                 ORDER BY week_start DESC,buyer_player_id,item_type""").fetchall()

    merged_player_rows={}
    for row in list(player_rows)+list(event_rows):
        week=str(row["week_start"] or "")
        item_type=str(row["item_type"] or "")
        pid=str(row["player_id"] or "").strip()
        if not week or item_type not in ("idol_orbs","splus_businesses") or not pid:
            continue
        key=(week,item_type,pid)
        quantity=max(0,int(row["quantity"] or 0))
        updated_at=max(0,int(row["updated_at"] or 0))
        current=merged_player_rows.get(key)
        if current is None:
            merged_player_rows[key]={
                "week_start":week,
                "lot_id":"",
                "item_type":item_type,
                "player_id":pid,
                "quantity":quantity,
                "updated_at":updated_at,
            }
        else:
            current["quantity"]=max(int(current["quantity"]),quantity)
            current["updated_at"]=max(int(current["updated_at"]),updated_at)
    player_rows=list(merged_player_rows.values())

    shared_by_week={}
'''
if old not in s:
    raise SystemExit("player rows query block missing")
s=s.replace(old,new,1)

old_return='''        "source":"game_actual",
        "counter_mode":"current_cycle_player_counters",
'''
new_return='''        "source":"game_actual",
        "counter_mode":"purchase_history_with_counter_fallback",
'''
if old_return not in s:
    raise SystemExit("history return mode missing")
s=s.replace(old_return,new_return,1)

# Add authenticated collector endpoint before the existing facts endpoint.
route='''            elif path == "/api/v1/clan-shop-facts/submit":
'''
new_route='''            elif path == "/api/v1/clan-shop-events/submit":
                origin = self.headers.get("Origin", "")
                if origin not in ALLOWED_ORIGINS:
                    self.send_json(HTTPStatus.FORBIDDEN, {"error": "origin_not_allowed"})
                    return
                collector_player_id = self.recipe_player()
                if not collector_player_id:
                    self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                    return
                try:
                    body = self.read_json(300_000)
                    result = submit_clan_shop_purchase_events(collector_player_id, body.get("rows"))
                    self.send_json(HTTPStatus.OK, result)
                except ValueError:
                    self.send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_clan_shop_events"})
            elif path == "/api/v1/clan-shop-facts/submit":
'''
if route not in s:
    raise SystemExit("facts submit route missing")
s=s.replace(route,new_route,1)

path.write_text(s,encoding="utf-8")
print("CLAN_SHOP_PURCHASE_EVENTS_V16_PATCH_OK")
