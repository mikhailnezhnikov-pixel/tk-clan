from pathlib import Path
import sys

target=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/server.py")
s=target.read_text(encoding="utf-8")

def need(old,label,count=1):
    actual=s.count(old)
    if actual!=count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")

def rep(old,new,label,count=1):
    global s
    need(old,label,count)
    s=s.replace(old,new,count)

if "HK_RUMORS_SHARED_RESULTS_R2" in s:
    print("HK_RUMORS_SHARED_RESULTS_R2_ALREADY_PRESENT")
    raise SystemExit(0)

anchor="HK_RUMORS_KOKKARAS_FEED_R1 = 'rumors-kokkaras-public-feed-20260925-r1'"
need(anchor,"Kokkaras feed marker")
s=s.replace(anchor,anchor+"\nHK_RUMORS_SHARED_RESULTS_R2 = 'rumors-shared-results-20260926-r2'",1)

table='''            CREATE TABLE IF NOT EXISTS rumor_routes (
                route_date TEXT PRIMARY KEY,
                source_text TEXT NOT NULL,
                routes_json TEXT NOT NULL,
                published_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
'''
need(table,"rumor_routes table")
s=s.replace(table,table+'''            CREATE TABLE IF NOT EXISTS rumor_observations (
                route_date TEXT NOT NULL,
                city_id TEXT NOT NULL,
                city_key TEXT NOT NULL DEFAULT '',
                city_name TEXT NOT NULL DEFAULT '',
                x INTEGER NOT NULL,
                y INTEGER NOT NULL,
                gamearea_id TEXT NOT NULL,
                rumor_id TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'hk',
                observed_at INTEGER NOT NULL,
                PRIMARY KEY(route_date,city_id,gamearea_id)
            );
            CREATE INDEX IF NOT EXISTS idx_rumor_observations_date
                ON rumor_observations(route_date,city_id,observed_at DESC);
''',1)

anchor2="def store_kokkaras_rumors(value: dict) -> None:"
i=s.find(anchor2)
if i<0: raise SystemExit("store_kokkaras_rumors missing")
next_def=s.find("\n\ndef ",i+len(anchor2))
if next_def<0: raise SystemExit("store_kokkaras_rumors end missing")
module=r'''

def rumor_observation_routes(db: sqlite3.Connection, route_date: str) -> list[dict]:
    rows = db.execute("""SELECT city_id,city_key,city_name,x,y,gamearea_id,rumor_id,observed_at
                         FROM rumor_observations
                         WHERE route_date=?
                         ORDER BY city_id,observed_at,gamearea_id""", (str(route_date),)).fetchall()
    grouped: dict[str, dict] = {}
    for row in rows:
        city_id = str(row["city_id"] or "")
        if not city_id:
            continue
        route = grouped.setdefault(city_id, {
            "city": str(row["city_name"] or row["city_key"] or city_id),
            "city_key": str(row["city_key"] or ""),
            "city_id": city_id,
            "group": "",
            "points": [],
            "source": "hk",
        })
        if len(route["points"]) >= 3:
            continue
        route["points"].append({
            "x": int(row["x"]),
            "y": int(row["y"]),
            "gamearea_id": str(row["gamearea_id"]),
            "area_ids": [str(row["gamearea_id"])],
            "rumor_id": str(row["rumor_id"] or ""),
            "source": "hk",
        })
    return list(grouped.values())


def merge_rumor_routes(primary: list[dict], supplemental: list[dict]) -> tuple[list[dict], int]:
    result = json.loads(json.dumps(primary or [], ensure_ascii=False))
    by_city = {str(row.get("city_id") or ""): row for row in result if str(row.get("city_id") or "")}
    added = 0
    for extra in supplemental or []:
        city_id = str(extra.get("city_id") or "")
        if not city_id:
            continue
        route = by_city.get(city_id)
        if route is None:
            route = json.loads(json.dumps(extra, ensure_ascii=False))
            route["source"] = "hk"
            route["points"] = []
            result.append(route)
            by_city[city_id] = route
        points = route.setdefault("points", [])
        known_ids = {str(p.get("gamearea_id") or "") for p in points if str(p.get("gamearea_id") or "")}
        known_xy = {(int(p.get("x", -9999)), int(p.get("y", -9999))) for p in points}
        for point in extra.get("points") or []:
            if len(points) >= 3:
                break
            gid = str(point.get("gamearea_id") or "")
            xy = (int(point.get("x", -9999)), int(point.get("y", -9999)))
            if (gid and gid in known_ids) or xy in known_xy:
                continue
            points.append(json.loads(json.dumps(point, ensure_ascii=False)))
            if gid:
                known_ids.add(gid)
            known_xy.add(xy)
            added += 1
    return result, added


def store_rumor_observation(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("invalid rumor observation")
    route_date = active_rumor_route_date()
    city_id = str(value.get("city_id") or "").strip()
    city_key = str(value.get("city_key") or "").strip()[:120]
    city_name = str(value.get("city_name") or "").strip()[:120]
    gamearea_id = str(value.get("gamearea_id") or "").strip()
    rumor_id = str(value.get("rumor_id") or "").strip()[:160]
    if not city_id or not gamearea_id or not ID_RE.fullmatch(city_id) or not ID_RE.fullmatch(gamearea_id):
        raise ValueError("invalid rumor ids")
    if "jackpot" not in rumor_id.casefold():
        raise ValueError("only jackpot observations are accepted")
    try:
        x = int(value.get("x"))
        y = int(value.get("y"))
    except (TypeError, ValueError) as error:
        raise ValueError("invalid rumor coordinates") from error
    if not (-500 <= x <= 500 and -500 <= y <= 500):
        raise ValueError("rumor coordinates out of range")
    now = utc_now()
    with db_session() as db:
        db.execute("""INSERT INTO rumor_observations(
                        route_date,city_id,city_key,city_name,x,y,gamearea_id,rumor_id,source,observed_at)
                      VALUES(?,?,?,?,?,?,?,?,?,?)
                      ON CONFLICT(route_date,city_id,gamearea_id) DO UPDATE SET
                        city_key=excluded.city_key,
                        city_name=excluded.city_name,
                        x=excluded.x,y=excluded.y,
                        rumor_id=excluded.rumor_id,
                        observed_at=MAX(rumor_observations.observed_at,excluded.observed_at)""",
                   (route_date,city_id,city_key,city_name,x,y,gamearea_id,rumor_id,"hk",now))
        count = db.execute("SELECT COUNT(*) FROM rumor_observations WHERE route_date=? AND city_id=?",
                           (route_date,city_id)).fetchone()[0]
    return {"ok":True,"date":route_date,"city_id":city_id,"known":min(3,int(count or 0))}


'''
s=s[:next_def]+module+s[next_def:]

route_anchor='''            elif path == "/api/v1/rumors/today":
                origin = self.headers.get("Origin", "")
'''
need(route_anchor,"rumors today branch")
report_branch='''            elif path == "/api/v1/rumors/report":
                origin = self.headers.get("Origin", "")
                if origin not in ALLOWED_ORIGINS:
                    self.send_json(HTTPStatus.FORBIDDEN, {"error":"origin_not_allowed"}); return
                if not self.recipe_player():
                    self.send_json(HTTPStatus.UNAUTHORIZED, {"error":"unauthorized"}); return
                body = self.read_json()
                try:
                    result = store_rumor_observation(body)
                except ValueError as error:
                    self.send_json(HTTPStatus.BAD_REQUEST, {"error":"bad_rumor_observation","detail":str(error)}); return
                self.send_json(HTTPStatus.OK, result)
'''
s=s.replace(route_anchor,report_branch+route_anchor,1)

# Merge HK observations into Kokkaras live results.
old_live='''                if remote and remote.get("date") == today and remote.get("routes"):
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
'''
new_live='''                if remote and remote.get("date") == today and remote.get("routes"):
                    routes = remote.get("routes") or []
                    with db_session() as db:
                        local_routes = rumor_observation_routes(db, today)
                        routes, local_added = merge_rumor_routes(routes, local_routes)
                        routes = enrich_rumor_routes(db, routes)
                    self.send_json(HTTPStatus.OK, {
                        "ok": True,
                        "date": today,
                        "published_at": int(remote.get("updated_ts") or 0),
                        "source_updated_at": remote.get("updated_at") or "",
                        "source": "kokkaras+hk" if local_added else "kokkaras",
                        "external_source": "kokkaras_public_rumors",
                        "local_added": int(local_added),
                        "invalid": int(remote.get("invalid") or 0),
                        "routes": routes,
                    })
                    return
'''
rep(old_live,new_live,"live route merge")

old_cached='''                with db_session() as db:
                    routes = enrich_rumor_routes(db, routes)
                cached_kokkaras = str(row["source_text"] or "").lstrip().upper().startswith("UPDATED_AT=")
                self.send_json(HTTPStatus.OK, {
                    "ok": True,
                    "date": row["route_date"],
                    "published_at": row["published_at"],
                    "source": "kokkaras-cache" if cached_kokkaras else "local",
                    "external_source": "kokkaras_public_rumors" if cached_kokkaras else "",
                    "routes": routes,
                })
'''
new_cached='''                with db_session() as db:
                    local_routes = rumor_observation_routes(db, today)
                    routes, local_added = merge_rumor_routes(routes, local_routes)
                    routes = enrich_rumor_routes(db, routes)
                cached_kokkaras = str(row["source_text"] or "").lstrip().upper().startswith("UPDATED_AT=")
                base_source = "kokkaras-cache" if cached_kokkaras else "local"
                self.send_json(HTTPStatus.OK, {
                    "ok": True,
                    "date": row["route_date"],
                    "published_at": row["published_at"],
                    "source": (base_source + "+hk") if local_added else base_source,
                    "external_source": "kokkaras_public_rumors" if cached_kokkaras else "",
                    "local_added": int(local_added),
                    "routes": routes,
                })
'''
rep(old_cached,new_cached,"cached route merge")

# No published route yet: still surface our own confirmed jackpot observations.
old_none='''                if not row:
                    self.send_json(HTTPStatus.OK, {"ok": True, "date": today, "source":"none", "routes": []})
                    return
'''
new_none='''                if not row:
                    with db_session() as db:
                        local_routes = rumor_observation_routes(db, today)
                        local_routes = enrich_rumor_routes(db, local_routes) if local_routes else []
                    self.send_json(HTTPStatus.OK, {
                        "ok": True, "date": today,
                        "source":"hk" if local_routes else "none",
                        "local_added": sum(len(r.get("points") or []) for r in local_routes),
                        "routes": local_routes,
                    })
                    return
'''
rep(old_none,new_none,"local-only fallback")

for marker in [
    "HK_RUMORS_SHARED_RESULTS_R2",
    "CREATE TABLE IF NOT EXISTS rumor_observations",
    "def rumor_observation_routes",
    "def merge_rumor_routes",
    "def store_rumor_observation",
    'path == "/api/v1/rumors/report"',
    '"source": "kokkaras+hk" if local_added else "kokkaras"',
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("RUMORS_SHARED_RESULTS_R2_PATCH=PASS")
