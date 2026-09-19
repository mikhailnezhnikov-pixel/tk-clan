from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text()
MARKER = "CLAN_SHOP_V1"
if MARKER in s:
    print("CLAN_SHOP_ALREADY_PRESENT")
    raise SystemExit(0)

functions = r'''
# CLAN_SHOP_V1
CLAN_SHOP_IDOL_LIMIT = 14
CLAN_SHOP_BUSINESS_LIMIT = 30
CLAN_SHOP_PER_PLAYER_LIMIT = 3


def ensure_clan_shop_schema() -> None:
    with db_session() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS clan_shop_allocations (
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
            CREATE INDEX IF NOT EXISTS idx_clan_shop_week
                ON clan_shop_allocations(week_start, updated_at);
            CREATE TABLE IF NOT EXISTS clan_shop_publications (
                week_start TEXT PRIMARY KEY,
                published_at INTEGER NOT NULL,
                published_by TEXT NOT NULL DEFAULT '',
                message_text TEXT NOT NULL DEFAULT ''
            );
        """)


def clan_shop_can_manage(member: dict | None) -> bool:
    return bool(member and member.get("maps_manage"))


def clan_shop_window(now_ts: int | None = None) -> dict:
    import datetime as _dt
    tz = _dt.timezone(_dt.timedelta(hours=9))
    now_value = int(now_ts if now_ts is not None else utc_now())
    local_now = _dt.datetime.fromtimestamp(now_value, _dt.timezone.utc).astimezone(tz)
    days_until_sunday = (6 - local_now.weekday()) % 7
    deadline_date = local_now.date() + _dt.timedelta(days=days_until_sunday)
    deadline = _dt.datetime.combine(deadline_date, _dt.time(21, 0), tzinfo=tz)
    if local_now >= deadline:
        deadline += _dt.timedelta(days=7)
    week_start_date = deadline.date() + _dt.timedelta(days=1)
    week_end_date = week_start_date + _dt.timedelta(days=6)
    return {
        "week_start": week_start_date.isoformat(),
        "week_end": week_end_date.isoformat(),
        "week_label": f"{week_start_date.strftime('%d.%m')}–{week_end_date.strftime('%d.%m.%Y')}",
        "deadline_at": int(deadline.timestamp()),
        "deadline_label": f"{deadline.strftime('%d.%m.%Y %H:%M')} GMT+9",
        "timezone": "GMT+9",
    }


def clan_shop_participants() -> list[dict]:
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


def clan_shop_payload(member: dict) -> dict:
    ensure_clan_shop_schema()
    window = clan_shop_window()
    participants = clan_shop_participants()
    week_start = window["week_start"]
    with db_session() as db:
        rows = db.execute("""SELECT player_key,idol_orbs,splus_businesses,updated_at
                             FROM clan_shop_allocations WHERE week_start=?""",
                          (week_start,)).fetchall()
        publication = db.execute("""SELECT published_at,published_by
                                    FROM clan_shop_publications WHERE week_start=?""",
                                 (week_start,)).fetchone()
    by_key = {str(row["player_key"]): row for row in rows}
    idol_total = 0
    business_total = 0
    for item in participants:
        row = by_key.get(item["player_key"])
        idol = int(row["idol_orbs"] or 0) if row else 0
        business = int(row["splus_businesses"] or 0) if row else 0
        item["idol_orbs"] = idol
        item["splus_businesses"] = business
        item["updated_at"] = int(row["updated_at"] or 0) if row else 0
        idol_total += idol
        business_total += business
    topic = telegram_delivery_target("clan_shop")
    return {
        "ok": True,
        "can_manage": clan_shop_can_manage(member),
        "window": window,
        "limits": {
            "idol_orbs": CLAN_SHOP_IDOL_LIMIT,
            "splus_businesses": CLAN_SHOP_BUSINESS_LIMIT,
            "per_player": CLAN_SHOP_PER_PLAYER_LIMIT,
        },
        "totals": {"idol_orbs": idol_total, "splus_businesses": business_total},
        "participants": participants,
        "published_at": int(publication["published_at"] or 0) if publication else 0,
        "published_by": str(publication["published_by"] or "") if publication else "",
        "topic_configured": bool(topic and topic.get("chat_id") and topic.get("thread_id") is not None),
    }


def set_clan_shop_allocation(member: dict, body: dict) -> dict:
    if not clan_shop_can_manage(member):
        raise PermissionError("clan shop manage denied")
    ensure_clan_shop_schema()
    window = clan_shop_window()
    week_start = window["week_start"]
    player_key = str(body.get("player_key") or "").strip()
    try:
        idol_orbs = int(body.get("idol_orbs") or 0)
        businesses = int(body.get("splus_businesses") or 0)
    except (TypeError, ValueError):
        raise ValueError("invalid quantity")
    if not (0 <= idol_orbs <= CLAN_SHOP_PER_PLAYER_LIMIT
            and 0 <= businesses <= CLAN_SHOP_PER_PLAYER_LIMIT):
        raise ValueError("invalid quantity")
    participants = {row["player_key"]: row for row in clan_shop_participants()}
    player = participants.get(player_key)
    if not player:
        raise LookupError("clan member not found")

    with db_session() as db:
        old = db.execute("""SELECT idol_orbs,splus_businesses FROM clan_shop_allocations
                            WHERE week_start=? AND player_key=?""",
                         (week_start, player_key)).fetchone()
        totals = db.execute("""SELECT COALESCE(SUM(idol_orbs),0) AS idols,
                                      COALESCE(SUM(splus_businesses),0) AS businesses
                               FROM clan_shop_allocations WHERE week_start=?""",
                            (week_start,)).fetchone()
        old_idols = int(old["idol_orbs"] or 0) if old else 0
        old_businesses = int(old["splus_businesses"] or 0) if old else 0
        next_idols = int(totals["idols"] or 0) - old_idols + idol_orbs
        next_businesses = int(totals["businesses"] or 0) - old_businesses + businesses
        if next_idols > CLAN_SHOP_IDOL_LIMIT:
            raise RuntimeError("idol_limit")
        if next_businesses > CLAN_SHOP_BUSINESS_LIMIT:
            raise RuntimeError("business_limit")
        if idol_orbs == 0 and businesses == 0:
            db.execute("""DELETE FROM clan_shop_allocations
                          WHERE week_start=? AND player_key=?""",
                       (week_start, player_key))
        else:
            db.execute("""INSERT INTO clan_shop_allocations(
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
                       (week_start, player_key, player["player_id"], player["nickname"],
                        idol_orbs, businesses, str(member.get("telegram_id") or ""), utc_now()))
    payload = clan_shop_payload(member)
    payload["saved_player_key"] = player_key
    return payload


def clan_shop_publication_text(payload: dict) -> str:
    participants = payload.get("participants") if isinstance(payload.get("participants"), list) else []
    window = payload["window"]
    idol_rows = [(row["nickname"], int(row.get("idol_orbs") or 0))
                 for row in participants if int(row.get("idol_orbs") or 0) > 0]
    business_rows = [(row["nickname"], int(row.get("splus_businesses") or 0))
                     for row in participants if int(row.get("splus_businesses") or 0) > 0]
    if not idol_rows and not business_rows:
        raise RuntimeError("empty")

    lines = [
        f"🛒 <b>Clan Shop — покупки на {html.escape(window['week_label'])}</b>",
        "",
    ]
    if idol_rows:
        idol_total = sum(value for _name, value in idol_rows)
        lines.append(f"🔮 <b>Шары идолов — {idol_total}/{CLAN_SHOP_IDOL_LIMIT}</b>")
        for name, value in idol_rows:
            lines.append(f"• {html.escape(name)} — {value}")
        lines.append("")
    if business_rows:
        business_total = sum(value for _name, value in business_rows)
        lines.append(f"🏢 <b>Бизнесы S+ — {business_total}/{CLAN_SHOP_BUSINESS_LIMIT}</b>")
        for name, value in business_rows:
            lines.append(f"• {html.escape(name)} — {value}")
        lines.append("")
    lines.append(f"Список на следующую неделю · дедлайн {html.escape(window['deadline_label'])}")
    return "\n".join(lines).strip()


def publish_clan_shop(member: dict) -> dict:
    if not clan_shop_can_manage(member):
        raise PermissionError("clan shop manage denied")
    target = telegram_delivery_target("clan_shop")
    if not target or not target.get("chat_id") or target.get("thread_id") is None:
        raise LookupError("clan shop topic not configured")
    payload = clan_shop_payload(member)
    text = clan_shop_publication_text(payload)
    delivered = telegram_send(str(target["chat_id"]), text,
                              message_thread_id=int(target["thread_id"]))
    if not delivered:
        raise OSError("telegram delivery failed")
    ensure_clan_shop_schema()
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
    result["published"] = True
    return result


'''

anchor = '\ndef page_shell(title: str, content: str) -> bytes:\n'
if anchor not in s:
    raise SystemExit("page_shell anchor missing")
s = s.replace(anchor, '\n' + functions + 'def page_shell(title: str, content: str) -> bytes:\n', 1)

# Add /setclanshop before the group-silence gate.
group_anchor = '''    # TELEGRAM_GROUP_SILENCE_V2
    # Group/forum messages must never start or continue a user flow.
'''
group_insert = '''    if command == "/setclanshop":
        if not telegram_can_configure_delivery(telegram_id):
            telegram_send(chat_id, "⛔ Недостаточно прав для настройки темы Clan Shop.",
                          message_thread_id=message.get("message_thread_id"))
            return
        thread_id = message.get("message_thread_id")
        if chat.get("type") != "supergroup" or thread_id is None:
            telegram_send(chat_id,
                          "Откройте тему «Clan Shop» и отправьте /setclanshop прямо внутри темы.")
            return
        save_telegram_delivery_target("clan_shop", chat_id, int(thread_id), telegram_id)
        telegram_send(chat_id,
                      "✅ Эта тема назначена для публикаций Clan Shop.",
                      message_thread_id=int(thread_id))
        return

    # TELEGRAM_GROUP_SILENCE_V2
    # Group/forum messages must never start or continue a user flow.
'''
if group_anchor not in s:
    raise SystemExit("group silence anchor missing")
s = s.replace(group_anchor, group_insert, 1)

# Add GET route for every cabinet member.
get_anchor = '''        elif path == "/api/v1/cabinet/maps":
            origin = self.headers.get("Origin", "")
'''
get_route = '''        elif path == "/api/v1/cabinet/clan-shop":
            origin = self.headers.get("Origin", "")
            if origin not in CABINET_ORIGINS:
                self.send_cabinet_json(HTTPStatus.FORBIDDEN, {"error": "origin_not_allowed"})
                return
            member = self.cabinet_member()
            if not member:
                self.send_cabinet_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            self.send_cabinet_json(HTTPStatus.OK, clan_shop_payload(member))
        elif path == "/api/v1/cabinet/maps":
            origin = self.headers.get("Origin", "")
'''
if get_anchor not in s:
    raise SystemExit("cabinet maps GET anchor missing")
s = s.replace(get_anchor, get_route, 1)

# Add POST save/publish routes before map mutations.
post_anchor = '''            elif path in ("/api/v1/cabinet/maps/publish", "/api/v1/cabinet/maps/member-access", "/api/v1/cabinet/maps/access-scope", "/api/v1/cabinet/maps/open-url"):
                origin = self.headers.get("Origin", "")
'''
post_route = '''            elif path in ("/api/v1/cabinet/clan-shop/set", "/api/v1/cabinet/clan-shop/publish"):
                origin = self.headers.get("Origin", "")
                if origin not in CABINET_ORIGINS:
                    self.send_cabinet_json(HTTPStatus.FORBIDDEN, {"error": "origin_not_allowed"}); return
                member = self.cabinet_member()
                if not member:
                    self.send_cabinet_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"}); return
                try:
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
                    self.send_cabinet_json(HTTPStatus.OK, result)
                except PermissionError:
                    self.send_cabinet_json(HTTPStatus.FORBIDDEN, {"error": "clan_shop_manage_denied"})
                except ValueError:
                    self.send_cabinet_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_quantity"})
                except LookupError as exc:
                    code = "clan_shop_topic_not_configured" if "topic" in str(exc) else "clan_member_not_found"
                    self.send_cabinet_json(HTTPStatus.NOT_FOUND, {"error": code})
                except RuntimeError as exc:
                    code = str(exc)
                    if code == "idol_limit":
                        code = "clan_shop_idol_limit"
                    elif code == "business_limit":
                        code = "clan_shop_business_limit"
                    elif code == "empty":
                        code = "clan_shop_empty"
                    self.send_cabinet_json(HTTPStatus.CONFLICT, {"error": code})
                except OSError:
                    self.send_cabinet_json(HTTPStatus.BAD_GATEWAY, {"error": "telegram_delivery_failed"})
            elif path in ("/api/v1/cabinet/maps/publish", "/api/v1/cabinet/maps/member-access", "/api/v1/cabinet/maps/access-scope", "/api/v1/cabinet/maps/open-url"):
                origin = self.headers.get("Origin", "")
'''
if post_anchor not in s:
    raise SystemExit("cabinet maps POST anchor missing")
s = s.replace(post_anchor, post_route, 1)

path.write_text(s)
print("CLAN_SHOP_PATCH_OK")
