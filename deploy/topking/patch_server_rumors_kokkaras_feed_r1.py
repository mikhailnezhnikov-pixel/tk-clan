from pathlib import Path
import sys

target=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/server.py")
s=target.read_text(encoding="utf-8")

def require(needle,label,count=None):
    actual=s.count(needle)
    if count is not None and actual!=count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")
    if actual<1:
        raise SystemExit(f"{label}: missing")

def replace(old,new,label,count=1):
    global s
    actual=s.count(old)
    if actual!=count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")
    s=s.replace(old,new,count)

if "HK_RUMORS_KOKKARAS_FEED_R1" in s:
    print("HK_RUMORS_KOKKARAS_FEED_R1_ALREADY_PRESENT")
    raise SystemExit(0)

# Standard-library HTTP client for the public Kokkaras feed.
if "import urllib.request" not in s:
    if s.startswith("#!"):
        nl=s.find("\n")
        s=s[:nl+1]+"import urllib.request\nimport urllib.error\n"+s[nl+1:]
    else:
        s="import urllib.request\nimport urllib.error\n"+s

const_anchor='RUMOR_TIMEZONE = timezone(timedelta(hours=RUMOR_UTC_OFFSET), name=f"UTC{RUMOR_UTC_OFFSET:+d}")'
require(const_anchor,"rumor timezone")
s=s.replace(const_anchor,const_anchor+"""
HK_RUMORS_KOKKARAS_FEED_R1 = 'rumors-kokkaras-public-feed-20260925-r1'
RUMOR_KOKKARAS_URL = os.environ.get("HK_RUMOR_KOKKARAS_URL", "https://kokkaras.com/hk_maps/rumors.php")
RUMOR_KOKKARAS_CACHE_TTL = max(5, int(os.environ.get("HK_RUMOR_KOKKARAS_CACHE_TTL", "20")))
RUMOR_KOKKARAS_LOCK = threading.Lock()
RUMOR_KOKKARAS_CACHE: dict[str, object] = {"fetched_at": 0, "value": None}
""",1)

parse_anchor="def parse_rumor_route(source_text: str) -> tuple[str, list[dict]]:"
require(parse_anchor,"parse_rumor_route")
module=r'''RUMOR_KOKKARAS_CITY_LABELS = {
    "city_name_moscow":"Moscow",
    "city_name_saint_petersburg":"Saint Petersburg",
    "city_name_minsk":"Minsk",
    "city_name_berlin":"Berlin",
    "city_name_london":"London",
    "city_name_paris":"Paris",
    "city_name_dubai":"Dubai",
    "city_name_tokyo":"Tokyo",
    "city_name_singapore":"Singapore",
    "city_name_new_york":"New York",
    "city_name_los_angeles":"Los Angeles",
    "city_name_boston":"Boston",
    "city_name_washington":"Washington",
    "city_name_rio_de_janeiro":"Rio de Janeiro",
    "city_name_lagos":"Lagos",
    "city_name_sydney":"Sydney",
    "city_name_auckland":"Auckland",
}


def kokkaras_rumor_route_date(updated: datetime) -> str:
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    athens = updated.astimezone(timezone(timedelta(hours=3)))
    if athens.hour < 15:
        athens -= timedelta(days=1)
    return athens.strftime("%Y-%m-%d")


def parse_kokkaras_rumors_text(source_text: str) -> dict:
    text = str(source_text or "").replace("\r", "")
    lines = [line.strip() for line in text.split("\n") if line.strip() and not line.lstrip().startswith("#")]
    if not lines:
        raise ValueError("empty Kokkaras rumors feed")
    match = re.match(r"^UPDATED_AT\s*=\s*(.+)$", lines[0], re.I)
    if not match:
        raise ValueError("Kokkaras UPDATED_AT missing")
    updated_raw = match.group(1).strip()
    try:
        updated = datetime.fromisoformat(updated_raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("invalid Kokkaras UPDATED_AT") from error

    grouped: dict[str, dict] = {}
    invalid = 0
    for line in lines[1:]:
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 5:
            invalid += 1
            continue
        city_key, city_id, y_raw, x_raw, gamearea_id = parts
        try:
            y, x = int(y_raw), int(x_raw)
        except ValueError:
            invalid += 1
            continue
        if not city_key or not city_id or not gamearea_id:
            invalid += 1
            continue
        route = grouped.setdefault(city_id, {
            "city": RUMOR_KOKKARAS_CITY_LABELS.get(city_key, city_key),
            "city_key": city_key,
            "city_id": city_id,
            "group": "",
            "points": [],
            "source": "kokkaras",
        })
        route["points"].append({
            "x": x,
            "y": y,
            "gamearea_id": gamearea_id,
            "area_ids": [gamearea_id],
            "source": "kokkaras",
        })

    routes = list(grouped.values())
    routes.sort(key=lambda row: list(RUMOR_KOKKARAS_CITY_LABELS).index(row["city_key"])
                if row.get("city_key") in RUMOR_KOKKARAS_CITY_LABELS else 999)
    if not routes:
        raise ValueError("Kokkaras rumors feed contains no routes")
    return {
        "date": kokkaras_rumor_route_date(updated),
        "updated_at": updated_raw,
        "updated_ts": int(updated.timestamp()),
        "routes": routes,
        "invalid": invalid,
        "source_text": text[:300000],
        "source": "kokkaras",
    }


def fetch_kokkaras_rumors(force: bool = False) -> dict | None:
    now = utc_now()
    with RUMOR_KOKKARAS_LOCK:
        cached = RUMOR_KOKKARAS_CACHE.get("value")
        fetched_at = int(RUMOR_KOKKARAS_CACHE.get("fetched_at") or 0)
        if cached and not force and now - fetched_at < RUMOR_KOKKARAS_CACHE_TTL:
            return cached if isinstance(cached, dict) else None
        request = urllib.request.Request(
            RUMOR_KOKKARAS_URL,
            headers={"User-Agent":"Mozilla/5.0 HK-Rumor-Sync/1.0", "Accept":"text/plain,*/*;q=0.8"},
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                raw = response.read(300001)
            if len(raw) > 300000:
                raise ValueError("Kokkaras rumors feed too large")
            value = parse_kokkaras_rumors_text(raw.decode("utf-8", "replace"))
            RUMOR_KOKKARAS_CACHE["value"] = value
            RUMOR_KOKKARAS_CACHE["fetched_at"] = now
            return value
        except Exception as error:
            RUMOR_KOKKARAS_CACHE["fetched_at"] = now
            if cached and isinstance(cached, dict):
                return cached
            raise RuntimeError(f"Kokkaras rumors feed unavailable: {error}") from error


def store_kokkaras_rumors(value: dict) -> None:
    route_date = str(value.get("date") or "")
    routes = value.get("routes")
    if not route_date or not isinstance(routes, list) or not routes:
        return
    published_at = int(value.get("updated_ts") or utc_now())
    with db_session() as db:
        db.execute("""INSERT INTO rumor_routes(route_date,source_text,routes_json,published_at,updated_at)
                      VALUES(?,?,?,?,?)
                      ON CONFLICT(route_date) DO UPDATE SET
                        source_text=excluded.source_text,
                        routes_json=excluded.routes_json,
                        published_at=excluded.published_at,
                        updated_at=excluded.updated_at
                      WHERE excluded.published_at >= rumor_routes.published_at""",
                   (route_date, str(value.get("source_text") or "")[:300000],
                    json.dumps(routes, ensure_ascii=False, separators=(",", ":")),
                    published_at, utc_now()))


'''
s=s.replace(parse_anchor,module+parse_anchor,1)

# Preserve direct gamearea ids received from Kokkaras instead of remapping them.
old_enrich='''        for point in route.get("points", []):
            matches = []
            for area in areas:'''
new_enrich='''        for point in route.get("points", []):
            direct_ids = [str(value) for value in (point.get("area_ids") or []) if str(value or "").strip()]
            direct_gamearea = str(point.get("gamearea_id") or "").strip()
            if direct_gamearea and direct_gamearea not in direct_ids:
                direct_ids.append(direct_gamearea)
            if direct_ids:
                point["area_ids"] = list(dict.fromkeys(direct_ids))
                continue
            matches = []
            for area in areas:'''
replace(old_enrich,new_enrich,"enrich direct Kokkaras ids")

old_route='''            elif path == "/api/v1/rumors/today":
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
                self.send_json(HTTPStatus.OK, {"ok": True, "date": row["route_date"], "published_at": row["published_at"], "routes": routes})'''
new_route='''            elif path == "/api/v1/rumors/today":
                origin = self.headers.get("Origin", "")
                if origin not in ALLOWED_ORIGINS:
                    self.send_json(HTTPStatus.FORBIDDEN, {"error":"origin_not_allowed"}); return
                if not self.recipe_player():
                    self.send_json(HTTPStatus.UNAUTHORIZED, {"error":"unauthorized"}); return
                self.read_json()
                today = active_rumor_route_date()
                remote = None
                try:
                    remote = fetch_kokkaras_rumors()
                    if remote and remote.get("date") == today and remote.get("routes"):
                        store_kokkaras_rumors(remote)
                except Exception as error:
                    remote = None

                if remote and remote.get("date") == today and remote.get("routes"):
                    routes = remote.get("routes") or []
                    with db_session() as db:
                        routes = enrich_rumor_routes(db, routes)
                    self.send_json(HTTPStatus.OK, {
                        "ok": True,
                        "date": today,
                        "published_at": int(remote.get("updated_ts") or 0),
                        "source_updated_at": remote.get("updated_at") or "",
                        "source": "kokkaras",
                        "external_source": "kokkaras_public_rumors",
                        "invalid": int(remote.get("invalid") or 0),
                        "routes": routes,
                    })
                    return

                with db_session() as db:
                    row = db.execute("SELECT route_date,source_text,routes_json,published_at FROM rumor_routes WHERE route_date=?", (today,)).fetchone()
                if not row:
                    self.send_json(HTTPStatus.OK, {"ok": True, "date": today, "source":"none", "routes": []})
                    return
                try:
                    routes = json.loads(row["routes_json"])
                except json.JSONDecodeError:
                    routes = []
                with db_session() as db:
                    routes = enrich_rumor_routes(db, routes)
                cached_kokkaras = str(row["source_text"] or "").lstrip().upper().startswith("UPDATED_AT=")
                self.send_json(HTTPStatus.OK, {
                    "ok": True,
                    "date": row["route_date"],
                    "published_at": row["published_at"],
                    "source": "kokkaras-cache" if cached_kokkaras else "local",
                    "external_source": "kokkaras_public_rumors" if cached_kokkaras else "",
                    "routes": routes,
                })'''
replace(old_route,new_route,"rumors today route")

for marker in [
    "HK_RUMORS_KOKKARAS_FEED_R1",
    "def parse_kokkaras_rumors_text",
    "def fetch_kokkaras_rumors",
    "def store_kokkaras_rumors",
    '"external_source": "kokkaras_public_rumors"',
    'point["area_ids"] = list(dict.fromkeys(direct_ids))',
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("RUMORS_KOKKARAS_FEED_R1_PATCH=PASS")
