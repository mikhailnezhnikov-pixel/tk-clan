from pathlib import Path

TARGET = Path('/tmp/server.py')
s = TARGET.read_text(encoding='utf-8')

REV = 'stage2g-rumors-server-20260919-r1'

def require(needle, message):
    if needle not in s:
        raise SystemExit(message)

require('def init_db() -> None:', 'init_db missing')
require('def canonical_map_area(', 'map canonicalizer missing')
require('def admin_action(self, path: str, form: dict[str, str]) -> None:', 'admin action missing')
require('elif path == "/admin/login":', 'POST routing anchor missing')

if f"HK_STAGE2G_RUMORS_SERVER_REV = '{REV}'" not in s:
    if 'from datetime import datetime, timezone' in s:
        s = s.replace('from datetime import datetime, timezone', 'from datetime import datetime, timedelta, timezone', 1)
    elif 'from datetime import datetime, timedelta, timezone' not in s:
        raise SystemExit('datetime import anchor missing')

    release_anchor = 'RELEASE_NOTES = os.environ.get("HK_RELEASE_NOTES", "Исправления и улучшения Hamster King Mobile.")[:1000]'
    require(release_anchor, 'release notes constant anchor missing')
    constants = (
        release_anchor + "\n"
        + f"HK_STAGE2G_RUMORS_SERVER_REV = '{REV}'\n"
        + 'RUMOR_UTC_OFFSET = int(os.environ.get("HK_RUMOR_UTC_OFFSET", "9"))\n'
        + 'RUMOR_TIMEZONE = timezone(timedelta(hours=RUMOR_UTC_OFFSET), name=f"UTC{RUMOR_UTC_OFFSET:+d}")'
    )
    s = s.replace(release_anchor, constants, 1)

if 'def active_rumor_route_date(' not in s:
    anchor = 'def version_tuple(value: str) -> tuple[int, ...] | None:'
    require(anchor, 'version_tuple anchor missing')
    helper = '''def active_rumor_route_date(now: datetime | None = None) -> str:
    """Return the route date for the 21:00-20:59 game-day window."""
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    local = moment.astimezone(RUMOR_TIMEZONE)
    if local.hour < 21:
        local -= timedelta(days=1)
    return local.strftime("%Y-%m-%d")


'''
    s = s.replace(anchor, helper + anchor, 1)

if 'CREATE TABLE IF NOT EXISTS rumor_routes (' not in s:
    anchor = '            CREATE TABLE IF NOT EXISTS user_settings ('
    require(anchor, 'user_settings table anchor missing')
    table = '''            CREATE TABLE IF NOT EXISTS rumor_routes (
                route_date TEXT PRIMARY KEY,
                source_text TEXT NOT NULL,
                routes_json TEXT NOT NULL,
                published_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
'''
    s = s.replace(anchor, table + anchor, 1)

if 'def parse_rumor_route(' not in s:
    anchor = 'def record_access('
    require(anchor, 'record_access anchor missing')
    parser = r'''def parse_rumor_route(source_text: str) -> tuple[str, list[dict]]:
    """Parse the compact daily route format pasted by the owner."""
    text = str(source_text or "").replace("\r", "")
    date_match = re.search(r"\b(\d{2})\.(\d{2})\.(\d{4})\b", text)
    if not date_match:
        raise ValueError("route date is required")
    day, month, year = date_match.groups()
    route_date = f"{year}-{month}-{day}"
    datetime.strptime(route_date, "%Y-%m-%d")
    group = ""
    rows: list[dict] = []
    for raw_line in text.split("\n"):
        line = raw_line.strip().replace("﹕", ":")
        if not line or line == "᠎":
            continue
        first, *rest = line.split(maxsplit=1)
        coords = re.findall(r"\b(\d{1,2}):(\d{2})\b", first)
        if coords and rest:
            city = rest[0].strip()
            points = [{"x": int(x), "y": int(y)} for x, y in coords]
            if city and points:
                rows.append({"group": group, "city": city[:80], "points": points})
            continue
        if not re.search(r"\d{1,2}:\d{2}", line) and not re.fullmatch(r"[■\sRUMORSСЛУХИ]+", line, re.I):
            group = line[:120]
    if not rows:
        raise ValueError("no rumor coordinates found")
    return route_date, rows


'''
    s = s.replace(anchor, parser + anchor, 1)

if 'def rumor_city_key(' not in s:
    anchor = 'def canonical_map_area('
    require(anchor, 'canonical map anchor missing')
    helpers = r'''def rumor_city_key(value: str) -> str:
    key = re.sub(r"[^a-zа-я0-9]+", " ", str(value or "").casefold().replace("ё", "е")).strip()
    aliases = {
        "москва":"moscow", "санкт петербург":"spb", "saint petersburg":"spb", "st petersburg":"spb",
        "минск":"minsk", "берлин":"berlin", "лондон":"london", "париж":"paris", "дубай":"dubai",
        "токио":"tokyo", "сингапур":"singapore", "нью йорк":"new york", "лос анджелес":"los angeles",
        "бостон":"boston", "вашингтон":"washington", "рио":"rio", "rio de janeiro":"rio",
        "рио де жанейро":"rio", "лагос":"lagos", "сидней":"sydney", "окленд":"auckland",
    }
    return aliases.get(key, key)


def enrich_rumor_routes(db: sqlite3.Connection, routes: list[dict]) -> list[dict]:
    areas = db.execute("SELECT area_id,city_id,city_name,x,y FROM map_areas WHERE x IS NOT NULL AND y IS NOT NULL").fetchall()
    alias_rows = db.execute("SELECT source_area_id,canonical_area_id FROM map_area_aliases").fetchall()
    aliases: dict[str, list[str]] = {}
    for row in alias_rows:
        aliases.setdefault(str(row["canonical_area_id"]), []).append(str(row["source_area_id"]))
    result = json.loads(json.dumps(routes, ensure_ascii=False))
    for route in result:
        wanted_city = rumor_city_key(route.get("city", ""))
        for point in route.get("points", []):
            matches = []
            for area in areas:
                city_keys = (rumor_city_key(area["city_name"]), rumor_city_key(area["city_id"]))
                if int(area["x"]) == int(point.get("x", -1)) and int(area["y"]) == int(point.get("y", -1)) and any(
                    wanted_city and (wanted_city in key or key in wanted_city) for key in city_keys if key
                ):
                    canonical = str(area["area_id"])
                    matches.extend(aliases.get(canonical, []))
                    matches.append(canonical)
            point["area_ids"] = list(dict.fromkeys(matches))
    return result


'''
    s = s.replace(anchor, helpers + anchor, 1)

if 'elif path == "/api/v1/rumors/today":' not in s:
    anchor = '            elif path == "/admin/login":'
    require(anchor, 'admin login POST anchor missing')
    route = '''            elif path == "/api/v1/rumors/today":
                origin = self.headers.get("Origin", "")
                if origin not in ALLOWED_ORIGINS:
                    self.send_json(HTTPStatus.FORBIDDEN, {"error":"origin_not_allowed"}); return
                if not self.recipe_player():
                    self.send_json(HTTPStatus.UNAUTHORIZED, {"error":"unauthorized"}); return
                self.read_json()
                today = active_rumor_route_date()
                with db_session() as db:
                    row = db.execute("SELECT route_date,routes_json,published_at FROM rumor_routes WHERE route_date=?", (today,)).fetchone()
                if not row:
                    self.send_json(HTTPStatus.OK, {"ok": True, "date": today, "routes": []})
                    return
                try:
                    routes = json.loads(row["routes_json"])
                except json.JSONDecodeError:
                    routes = []
                with db_session() as db:
                    routes = enrich_rumor_routes(db, routes)
                self.send_json(HTTPStatus.OK, {"ok": True, "date": row["route_date"], "published_at": row["published_at"], "routes": routes})
'''
    s = s.replace(anchor, route + anchor, 1)

if 'rumor_row = db.execute("SELECT route_date,source_text,published_at FROM rumor_routes ORDER BY route_date DESC LIMIT 1").fetchone()' not in s:
    anchor = '            member_rows = db.execute('
    require(anchor, 'admin member query anchor missing')
    line = '            rumor_row = db.execute("SELECT route_date,source_text,published_at FROM rumor_routes ORDER BY route_date DESC LIMIT 1").fetchone()\n'
    s = s.replace(anchor, line + anchor, 1)

if 'rumor_text = html.escape(rumor_row["source_text"] if rumor_row else "", quote=False)' not in s:
    anchor = '        content = f"""<div style="display:flex;justify-content:space-between;gap:12px;align-items:center">'
    require(anchor, 'admin content anchor missing')
    vars_block = (
        '        rumor_text = html.escape(rumor_row["source_text"] if rumor_row else "", quote=False)\n'
        '        rumor_status = f"Опубликован маршрут на <b>{html.escape(rumor_row[\'route_date\'])}</b> · {iso_time(rumor_row[\'published_at\'])}" if rumor_row else "Маршрут ещё не опубликован"\n'
    )
    s = s.replace(anchor, vars_block + anchor, 1)

rumor_card = '''        <div class=card><h2>Маршрут слухов на день</h2><p class=muted>{rumor_status}. Вставьте текст целиком: дата, затем строки «координаты Город». Регионы распознаются автоматически.</p><form method=post action=/admin/rumors/publish><textarea name=route_text required rows=18 style="width:100%;box-sizing:border-box;font:14px ui-monospace,monospace">{rumor_text}</textarea><div class=actions style="margin-top:10px"><button class=primary>Опубликовать маршрут</button></div></form></div>
'''
if '<h2>Маршрут слухов на день</h2>' not in s:
    anchor = '        <div class=card><h2>Доступ в личный кабинет</h2>'
    require(anchor, 'admin cabinet card anchor missing')
    s = s.replace(anchor, rumor_card + anchor, 1)

if 'if path == "/admin/rumors/publish":' not in s:
    anchor = '    def admin_action(self, path: str, form: dict[str, str]) -> None:\n'
    require(anchor, 'admin_action definition missing')
    branch = '''    def admin_action(self, path: str, form: dict[str, str]) -> None:
        if path == "/admin/rumors/publish":
            try:
                route_date, routes = parse_rumor_route(form.get("route_text", ""))
                now = utc_now()
                with db_session() as db:
                    db.execute("""INSERT INTO rumor_routes(route_date,source_text,routes_json,published_at,updated_at)
                                  VALUES(?,?,?,?,?) ON CONFLICT(route_date) DO UPDATE SET source_text=excluded.source_text,
                                  routes_json=excluded.routes_json,published_at=excluded.published_at,updated_at=excluded.updated_at""",
                               (route_date, form.get("route_text", "")[:20000], json.dumps(routes, ensure_ascii=False, separators=(",", ":")), now, now))
                audit("rumors_publish", route_date, self.client_ip(), f"cities={len(routes)} points={sum(len(row['points']) for row in routes)}")
            except ValueError as error:
                audit("rumors_publish_failed", "", self.client_ip(), str(error))
            self.redirect("/admin")
            return
'''
    s = s.replace(anchor, branch, 1)

checks = [
    (f"HK_STAGE2G_RUMORS_SERVER_REV = '{REV}'", 'Rumors server marker missing'),
    ('from datetime import datetime, timedelta, timezone', 'timedelta import missing'),
    ('CREATE TABLE IF NOT EXISTS rumor_routes (', 'rumor_routes table missing'),
    ('def active_rumor_route_date(', 'rumor game-day helper missing'),
    ('def parse_rumor_route(', 'rumor route parser missing'),
    ('def enrich_rumor_routes(', 'rumor map enrichment missing'),
    ('elif path == "/api/v1/rumors/today":', 'Rumors API missing'),
    ('if path == "/admin/rumors/publish":', 'Rumors admin publisher missing'),
    ('<h2>Маршрут слухов на день</h2>', 'Rumors admin card missing'),
]
for needle,message in checks:
    require(needle,message)

TARGET.write_text(s,encoding='utf-8')
