from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text()
MARKER = "CLAN_SHOP_REQUESTS_V2"
if MARKER in s:
    print("CLAN_SHOP_REQUESTS_ALREADY_PRESENT")
    raise SystemExit(0)

# Extend schema with player requests.
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
            CREATE TABLE IF NOT EXISTS clan_shop_requests (
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
if old_schema not in s:
    raise SystemExit("clan shop schema anchor missing")
s = s.replace(old_schema, new_schema, 1)

# Switch weekly deadline to Moscow time.
old_window = '''    tz = _dt.timezone(_dt.timedelta(hours=9))
    now_value = int(now_ts if now_ts is not None else utc_now())
    local_now = _dt.datetime.fromtimestamp(now_value, _dt.timezone.utc).astimezone(tz)
'''
new_window = '''    # CLAN_SHOP_REQUESTS_V2
    # Clan Shop week closes Sunday at 21:00 Moscow time (UTC+3).
    tz = _dt.timezone(_dt.timedelta(hours=3))
    now_value = int(now_ts if now_ts is not None else utc_now())
    local_now = _dt.datetime.fromtimestamp(now_value, _dt.timezone.utc).astimezone(tz)
'''
if old_window not in s:
    raise SystemExit("clan shop timezone anchor missing")
s = s.replace(old_window, new_window, 1)
s = s.replace('"deadline_label": f"{deadline.strftime(\'%d.%m.%Y %H:%M\')} GMT+9",\n        "timezone": "GMT+9",',
              '"deadline_label": f"{deadline.strftime(\'%d.%m.%Y %H:%M\')} MSK",\n        "timezone": "GMT+3",', 1)

# Add request data to payload.
old_payload_query = '''        publication = db.execute("""SELECT published_at,published_by
                                    FROM clan_shop_publications WHERE week_start=?""",
                                 (week_start,)).fetchone()
    by_key = {str(row["player_key"]): row for row in rows}
'''
new_payload_query = '''        publication = db.execute("""SELECT published_at,published_by
                                    FROM clan_shop_publications WHERE week_start=?""",
                                 (week_start,)).fetchone()
        request_rows = db.execute("""SELECT player_key,idol_orbs,splus_businesses,updated_at
                                     FROM clan_shop_requests WHERE week_start=?""",
                                  (week_start,)).fetchall()
    by_key = {str(row["player_key"]): row for row in rows}
    request_by_key = {str(row["player_key"]): row for row in request_rows}
'''
if old_payload_query not in s:
    raise SystemExit("payload query anchor missing")
s = s.replace(old_payload_query, new_payload_query, 1)

old_loop = '''        item["idol_orbs"] = idol
        item["splus_businesses"] = business
        item["updated_at"] = int(row["updated_at"] or 0) if row else 0
        idol_total += idol
        business_total += business
'''
new_loop = '''        item["idol_orbs"] = idol
        item["splus_businesses"] = business
        item["updated_at"] = int(row["updated_at"] or 0) if row else 0
        request = request_by_key.get(item["player_key"])
        item["request_idol_orbs"] = int(request["idol_orbs"] or 0) if request else 0
        item["request_splus_businesses"] = int(request["splus_businesses"] or 0) if request else 0
        item["request_updated_at"] = int(request["updated_at"] or 0) if request else 0
        idol_total += idol
        business_total += business
'''
if old_loop not in s:
    raise SystemExit("payload participant loop anchor missing")
s = s.replace(old_loop, new_loop, 1)

old_return_tail = '''        "published_by": str(publication["published_by"] or "") if publication else "",
        "topic_configured": bool(topic and topic.get("chat_id") and topic.get("thread_id") is not None),
    }
'''
new_return_tail = '''        "published_by": str(publication["published_by"] or "") if publication else "",
        "topic_configured": bool(topic and topic.get("chat_id") and topic.get("thread_id") is not None),
        "my_player_id": str(member.get("linked_player_id") or ""),
        "requests_open": utc_now() < int(window["deadline_at"]),
    }
'''
if old_return_tail not in s:
    raise SystemExit("payload return anchor missing")
s = s.replace(old_return_tail, new_return_tail, 1)

# Add request save and accept helpers before set_clan_shop_allocation.
anchor = '\ndef set_clan_shop_allocation(member: dict, body: dict) -> dict:\n'
helpers = r'''
def set_clan_shop_request(member: dict, body: dict) -> dict:
    ensure_clan_shop_schema()
    window = clan_shop_window()
    if utc_now() >= int(window["deadline_at"]):
        raise RuntimeError("requests_closed")
    player_id = str(member.get("linked_player_id") or "").strip()
    if not player_id:
        raise PermissionError("player link required")
    participants = clan_shop_participants()
    player = next((row for row in participants if row["player_id"] == player_id), None)
    if not player:
        raise LookupError("clan member not found")
    try:
        idol_orbs = int(body.get("idol_orbs") or 0)
        businesses = int(body.get("splus_businesses") or 0)
    except (TypeError, ValueError):
        raise ValueError("invalid quantity")
    if not (0 <= idol_orbs <= CLAN_SHOP_PER_PLAYER_LIMIT
            and 0 <= businesses <= CLAN_SHOP_PER_PLAYER_LIMIT):
        raise ValueError("invalid quantity")
    with db_session() as db:
        if idol_orbs == 0 and businesses == 0:
            db.execute("""DELETE FROM clan_shop_requests
                          WHERE week_start=? AND player_key=?""",
                       (window["week_start"], player["player_key"]))
        else:
            db.execute("""INSERT INTO clan_shop_requests(
                            week_start,player_key,player_id,nickname,idol_orbs,splus_businesses,
                            updated_by,updated_at)
                          VALUES(?,?,?,?,?,?,?,?)
                          ON CONFLICT(week_start,player_key) DO UPDATE SET
                            player_id=excluded.player_id,
                            nickname=excluded.nickname,
                            idol_orbs=excluded.idol_orbs,
                            splus_businesses=excluded.splus_businesses,
                            updated_by=excluded.updated_by,
                            updated_at=excluded.updated_at""",
                       (window["week_start"], player["player_key"], player["player_id"],
                        player["nickname"], idol_orbs, businesses,
                        str(member.get("telegram_id") or ""), utc_now()))
    return clan_shop_payload(member)


def accept_clan_shop_request(member: dict, body: dict) -> dict:
    if not clan_shop_can_manage(member):
        raise PermissionError("clan shop manage denied")
    ensure_clan_shop_schema()
    window = clan_shop_window()
    player_key = str(body.get("player_key") or "").strip()
    item = str(body.get("item") or "").strip()
    if item not in ("idol_orbs", "splus_businesses"):
        raise ValueError("invalid item")
    with db_session() as db:
        request = db.execute("""SELECT idol_orbs,splus_businesses
                                FROM clan_shop_requests
                                WHERE week_start=? AND player_key=?""",
                             (window["week_start"], player_key)).fetchone()
    if not request:
        raise LookupError("request not found")
    requested = int(request[item] or 0)
    if requested <= 0:
        raise LookupError("request not found")

    payload = clan_shop_payload(member)
    player = next((row for row in payload["participants"]
                   if row["player_key"] == player_key), None)
    if not player:
        raise LookupError("clan member not found")

    new_idols = requested if item == "idol_orbs" else int(player.get("idol_orbs") or 0)
    new_businesses = requested if item == "splus_businesses" else int(player.get("splus_businesses") or 0)
    return set_clan_shop_allocation(member, {
        "player_key": player_key,
        "idol_orbs": new_idols,
        "splus_businesses": new_businesses,
    })


'''
if anchor not in s:
    raise SystemExit("allocation function anchor missing")
s = s.replace(anchor, '\n' + helpers + 'def set_clan_shop_allocation(member: dict, body: dict) -> dict:\n', 1)

# Expand POST routes.
old_routes = '''            elif path in ("/api/v1/cabinet/clan-shop/set", "/api/v1/cabinet/clan-shop/publish"):
                origin = self.headers.get("Origin", "")
'''
new_routes = '''            elif path in ("/api/v1/cabinet/clan-shop/set",
                             "/api/v1/cabinet/clan-shop/request",
                             "/api/v1/cabinet/clan-shop/accept-request",
                             "/api/v1/cabinet/clan-shop/publish"):
                origin = self.headers.get("Origin", "")
'''
if old_routes not in s:
    raise SystemExit("clan shop POST route anchor missing")
s = s.replace(old_routes, new_routes, 1)

old_try = '''                try:
                    if path.endswith("/set"):
                        body = self.read_json(8192)
                        result = set_clan_shop_allocation(member, body)
                        audit("cabinet_clan_shop_set", str(body.get("player_key", "")),
                              self.client_ip(),
                              f"idols={body.get('idol_orbs',0)} businesses={body.get('splus_businesses',0)}")
                    else:
                        result = publish_clan_shop(member)
                        audit("cabinet_clan_shop_publish", result["window"]["week_start"],
                              self.client_ip(),
                              f"idols={result['totals']['idol_orbs']} businesses={result['totals']['splus_businesses']}")
'''
new_try = '''                try:
                    if path.endswith("/set"):
                        body = self.read_json(8192)
                        result = set_clan_shop_allocation(member, body)
                        audit("cabinet_clan_shop_set", str(body.get("player_key", "")),
                              self.client_ip(),
                              f"idols={body.get('idol_orbs',0)} businesses={body.get('splus_businesses',0)}")
                    elif path.endswith("/request"):
                        body = self.read_json(4096)
                        result = set_clan_shop_request(member, body)
                        audit("cabinet_clan_shop_request", str(member.get("linked_player_id") or ""),
                              self.client_ip(),
                              f"idols={body.get('idol_orbs',0)} businesses={body.get('splus_businesses',0)}")
                    elif path.endswith("/accept-request"):
                        body = self.read_json(4096)
                        result = accept_clan_shop_request(member, body)
                        audit("cabinet_clan_shop_accept_request", str(body.get("player_key", "")),
                              self.client_ip(), str(body.get("item", "")))
                    else:
                        result = publish_clan_shop(member)
                        audit("cabinet_clan_shop_publish", result["window"]["week_start"],
                              self.client_ip(),
                              f"idols={result['totals']['idol_orbs']} businesses={result['totals']['splus_businesses']}")
'''
if old_try not in s:
    raise SystemExit("clan shop POST try anchor missing")
s = s.replace(old_try, new_try, 1)

# Map special errors.
old_runtime = '''                except RuntimeError as exc:
                    code = str(exc)
                    if code == "idol_limit":
                        code = "clan_shop_idol_limit"
                    elif code == "business_limit":
                        code = "clan_shop_business_limit"
                    elif code == "empty":
                        code = "clan_shop_empty"
                    self.send_cabinet_json(HTTPStatus.CONFLICT, {"error": code})
'''
new_runtime = '''                except RuntimeError as exc:
                    code = str(exc)
                    if code == "idol_limit":
                        code = "clan_shop_idol_limit"
                    elif code == "business_limit":
                        code = "clan_shop_business_limit"
                    elif code == "empty":
                        code = "clan_shop_empty"
                    elif code == "requests_closed":
                        code = "clan_shop_requests_closed"
                    self.send_cabinet_json(HTTPStatus.CONFLICT, {"error": code})
'''
if old_runtime not in s:
    raise SystemExit("runtime error anchor missing")
s = s.replace(old_runtime, new_runtime, 1)

# Distinguish player-link permission.
old_perm = '''                except PermissionError:
                    self.send_cabinet_json(HTTPStatus.FORBIDDEN, {"error": "clan_shop_manage_denied"})
'''
new_perm = '''                except PermissionError as exc:
                    code = "player_link_required" if "player link" in str(exc) else "clan_shop_manage_denied"
                    self.send_cabinet_json(HTTPStatus.FORBIDDEN, {"error": code})
'''
if old_perm not in s:
    raise SystemExit("permission error anchor missing")
s = s.replace(old_perm, new_perm, 1)

path.write_text(s)
print("CLAN_SHOP_REQUESTS_PATCH_OK")
