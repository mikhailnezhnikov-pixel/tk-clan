from pathlib import Path
import sys

target = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/server.py")
s = target.read_text(encoding="utf-8")

def need(old, label, count=1):
    actual = s.count(old)
    if actual != count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")

if "HK_RUMORS_COORDINATOR_R3" in s:
    print("HK_RUMORS_COORDINATOR_R3_ALREADY_PRESENT")
    raise SystemExit(0)

shared_marker = "HK_RUMORS_SHARED_RESULTS_R2 = 'rumors-shared-results-20260926-r2'"
need(shared_marker, "shared results marker")
s = s.replace(
    shared_marker,
    shared_marker + "\nHK_RUMORS_COORDINATOR_R3 = 'rumors-coordinator-kokkaras-v40-20260926-r3'",
    1,
)

schema_anchor = """            CREATE INDEX IF NOT EXISTS idx_rumor_observations_date
                ON rumor_observations(route_date,city_id,observed_at DESC);
"""
need(schema_anchor, "rumor observations schema")
schema = """            CREATE TABLE IF NOT EXISTS rumor_hunter_presence (
                cycle_id TEXT NOT NULL,
                clan_id TEXT NOT NULL,
                player_id TEXT NOT NULL,
                nickname TEXT NOT NULL DEFAULT '',
                ready INTEGER NOT NULL DEFAULT 0,
                unlocked_json TEXT NOT NULL DEFAULT '[]',
                timezone TEXT NOT NULL DEFAULT '',
                last_seen INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                PRIMARY KEY(cycle_id,clan_id,player_id)
            );
            CREATE INDEX IF NOT EXISTS idx_rumor_hunter_presence_live
                ON rumor_hunter_presence(cycle_id,clan_id,ready,last_seen DESC);
            CREATE TABLE IF NOT EXISTS rumor_hunter_cities (
                cycle_id TEXT NOT NULL,
                clan_id TEXT NOT NULL,
                city_id TEXT NOT NULL,
                city_key TEXT NOT NULL DEFAULT '',
                city_name TEXT NOT NULL DEFAULT '',
                city_order INTEGER NOT NULL DEFAULT 999,
                status TEXT NOT NULL DEFAULT 'unassigned',
                assigned_player_id TEXT NOT NULL DEFAULT '',
                lease_token TEXT NOT NULL DEFAULT '',
                lease_until INTEGER NOT NULL DEFAULT 0,
                probes INTEGER NOT NULL DEFAULT 0,
                posts INTEGER NOT NULL DEFAULT 0,
                wait409 INTEGER NOT NULL DEFAULT 0,
                jackpots_json TEXT NOT NULL DEFAULT '[]',
                updated_at INTEGER NOT NULL,
                completed_at INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(cycle_id,clan_id,city_id)
            );
            CREATE INDEX IF NOT EXISTS idx_rumor_hunter_cities_state
                ON rumor_hunter_cities(cycle_id,clan_id,status,city_order);
            CREATE TABLE IF NOT EXISTS rumor_hunter_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id TEXT NOT NULL,
                clan_id TEXT NOT NULL,
                player_id TEXT NOT NULL DEFAULT '',
                city_id TEXT NOT NULL DEFAULT '',
                event TEXT NOT NULL,
                detail_json TEXT NOT NULL DEFAULT '{}',
                created_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_rumor_hunter_history_cycle
                ON rumor_hunter_history(cycle_id,clan_id,created_at DESC);
"""
s = s.replace(schema_anchor, schema_anchor + schema, 1)

helper_anchor = "def store_rumor_observation(value: object) -> dict:"
need(helper_anchor, "store_rumor_observation helper")

module = r'''
RUMOR_HUNTER_LEASE_SECONDS = 90
RUMOR_HUNTER_PRESENCE_SECONDS = 55
RUMOR_HUNTER_CITIES = [
    ("aa3d99b6-054c-4add-a825-437eea6514be","city_name_moscow","Moscow"),
    ("cac5d303-8251-4c5c-b5b1-0a3cb7789863","city_name_saint_petersburg","St. Petersburg"),
    ("beb0a9a3-f4bd-4213-8285-429e9f0f064e","city_name_minsk","Minsk"),
    ("165263b1-411c-4ce4-80b9-fbf5068d5b7c","city_name_berlin","Berlin"),
    ("caa3ccf0-cecd-4376-93f8-d11780859431","city_name_london","London"),
    ("0b07d8ca-3ad1-4e9f-80b7-fb59aeda5544","city_name_paris","Paris"),
    ("7b396fb3-2d66-4afd-85e4-98b9fd58a90a","city_name_dubai","Dubai"),
    ("b5419fbd-f88b-4776-8106-ba7772be4370","city_name_tokyo","Tokyo"),
    ("04d866e2-f582-4e4f-9faf-2722aec5cc17","city_name_singapore","Singapore"),
    ("bcb09d51-bad7-4ddf-a564-e6003ff9745f","city_name_new_york","New York"),
    ("055abb57-8d7d-417c-b9f1-94766fc0eb44","city_name_los_angeles","Los Angeles"),
    ("8184938e-f2e6-453c-9e0d-a16d87cbe46c","city_name_boston","Boston"),
    ("676c067f-ba9f-4f92-a150-9fd50dc2948d","city_name_washington","Washington"),
    ("3848bf1f-ba0e-4def-b4e1-7cd30f79406e","city_name_rio_de_janeiro","Rio de Janeiro"),
    ("a4a86f1e-70c4-43fa-b804-2a358dc6ae87","city_name_lagos","Lagos"),
    ("a98d8ea6-aac2-49ef-8c8c-8b50471a6c84","city_name_sydney","Sydney"),
    ("2cf24eee-6245-4692-bea5-daf949c063dc","city_name_auckland","Auckland"),
]
RUMOR_HUNTER_CITY_IDS = {row[0] for row in RUMOR_HUNTER_CITIES}
RUMOR_HUNTER_CITY_META = {
    row[0]: {"city_key": row[1], "city_name": row[2], "order": index}
    for index, row in enumerate(RUMOR_HUNTER_CITIES)
}


def rumor_hunter_id(value: object, label: str) -> str:
    text = str(value or "").strip()
    if not text or not ID_RE.fullmatch(text):
        raise ValueError(f"invalid {label}")
    return text


def rumor_hunter_unlocked(value: object) -> list[str]:
    rows = value if isinstance(value, list) else []
    return [str(city_id) for city_id in rows if str(city_id) in RUMOR_HUNTER_CITY_IDS][:17]


def rumor_hunter_history_add(
    db: sqlite3.Connection, cycle_id: str, clan_id: str, player_id: str,
    city_id: str, event: str, detail: dict | None = None
) -> None:
    db.execute(
        """INSERT INTO rumor_hunter_history(
             cycle_id,clan_id,player_id,city_id,event,detail_json,created_at)
             VALUES(?,?,?,?,?,?,?)""",
        (
            cycle_id, clan_id, str(player_id or ""), str(city_id or ""),
            str(event or "")[:80],
            json.dumps(detail or {}, ensure_ascii=False, separators=(",", ":"))[:12000],
            utc_now(),
        ),
    )


def rumor_hunter_shared_routes(route_date: str) -> list[dict]:
    routes: list[dict] = []
    try:
        remote = fetch_kokkaras_rumors(force=False)
        if remote and str(remote.get("date") or "") == route_date and remote.get("routes"):
            routes = remote.get("routes") or []
            try:
                store_kokkaras_rumors(remote)
            except Exception:
                pass
    except Exception:
        pass

    with db_session() as db:
        if not routes:
            row = db.execute(
                "SELECT routes_json FROM rumor_routes WHERE route_date=?", (route_date,)
            ).fetchone()
            if row:
                try:
                    routes = json.loads(row["routes_json"] or "[]")
                except (TypeError, json.JSONDecodeError):
                    routes = []
        local_routes = rumor_observation_routes(db, route_date)
        routes, _ = merge_rumor_routes(routes, local_routes)
    return routes


def rumor_hunter_known_map(route_date: str) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for route in rumor_hunter_shared_routes(route_date):
        city_id = str(route.get("city_id") or "")
        if city_id not in RUMOR_HUNTER_CITY_IDS:
            continue
        points = []
        seen: set[tuple[str, int, int]] = set()
        for point in route.get("points") or []:
            gamearea_id = str(point.get("gamearea_id") or "").strip()
            try:
                x, y = int(point.get("x")), int(point.get("y"))
            except (TypeError, ValueError):
                continue
            if not gamearea_id:
                continue
            key = (gamearea_id, x, y)
            if key in seen:
                continue
            seen.add(key)
            points.append({
                "x": x,
                "y": y,
                "gamearea_id": gamearea_id,
                "rumor_id": str(point.get("rumor_id") or "rumor_jackpot_known"),
                "source": str(point.get("source") or route.get("source") or "shared"),
            })
            if len(points) >= 3:
                break
        if points:
            meta = RUMOR_HUNTER_CITY_META[city_id]
            result[city_id] = {
                "city_id": city_id,
                "city_key": str(route.get("city_key") or meta["city_key"]),
                "city_name": str(route.get("city") or meta["city_name"]),
                "points": points,
            }
    return result


def rumor_hunter_seed(db: sqlite3.Connection, cycle_id: str, clan_id: str, now: int) -> None:
    for city_id, city_key, city_name in RUMOR_HUNTER_CITIES:
        db.execute(
            """INSERT OR IGNORE INTO rumor_hunter_cities(
               cycle_id,clan_id,city_id,city_key,city_name,city_order,status,updated_at)
               VALUES(?,?,?,?,?,?,?,?)""",
            (
                cycle_id, clan_id, city_id, city_key, city_name,
                RUMOR_HUNTER_CITY_META[city_id]["order"], "unassigned", now,
            ),
        )


def rumor_hunter_rebalance(
    db: sqlite3.Connection, cycle_id: str, clan_id: str,
    known: dict[str, dict], now: int
) -> None:
    rumor_hunter_seed(db, cycle_id, clan_id, now)
    cutoff = now - RUMOR_HUNTER_PRESENCE_SECONDS

    db.execute(
        """UPDATE rumor_hunter_presence SET ready=0,updated_at=?
           WHERE cycle_id=? AND clan_id=? AND ready=1 AND last_seen<?""",
        (now, cycle_id, clan_id, cutoff),
    )
    db.execute(
        """UPDATE rumor_hunter_cities
           SET status='queued',lease_token='',lease_until=0,updated_at=?
           WHERE cycle_id=? AND clan_id=? AND status='running'
             AND lease_until>0 AND lease_until<?""",
        (now, cycle_id, clan_id, now),
    )

    for city_id, row in known.items():
        points = row.get("points") or []
        if len(points) < 3:
            continue
        db.execute(
            """UPDATE rumor_hunter_cities
               SET status='done',assigned_player_id='',lease_token='',lease_until=0,
                   jackpots_json=?,
                   completed_at=CASE WHEN completed_at>0 THEN completed_at ELSE ? END,
                   updated_at=?
               WHERE cycle_id=? AND clan_id=? AND city_id=?""",
            (
                json.dumps(points[:3], ensure_ascii=False, separators=(",", ":")),
                now, now, cycle_id, clan_id, city_id,
            ),
        )

    ready_rows = db.execute(
        """SELECT player_id,unlocked_json FROM rumor_hunter_presence
           WHERE cycle_id=? AND clan_id=? AND ready=1 AND last_seen>=?
           ORDER BY last_seen DESC,player_id""",
        (cycle_id, clan_id, cutoff),
    ).fetchall()

    ready: dict[str, set[str]] = {}
    for row in ready_rows:
        try:
            unlocked = {str(value) for value in json.loads(row["unlocked_json"] or "[]")}
        except (TypeError, json.JSONDecodeError):
            unlocked = set()
        ready[str(row["player_id"])] = unlocked & RUMOR_HUNTER_CITY_IDS

    cities = db.execute(
        """SELECT city_id,status,assigned_player_id,lease_until
           FROM rumor_hunter_cities
           WHERE cycle_id=? AND clan_id=? ORDER BY city_order""",
        (cycle_id, clan_id),
    ).fetchall()

    load = {player_id: 0 for player_id in ready}
    for row in cities:
        city_id = str(row["city_id"])
        player_id = str(row["assigned_player_id"] or "")
        if row["status"] in ("queued", "running") and player_id in ready and city_id in ready[player_id]:
            load[player_id] += 1

    for row in cities:
        city_id = str(row["city_id"])
        status = str(row["status"] or "")
        if status == "done":
            continue
        current = str(row["assigned_player_id"] or "")
        if (
            status == "running"
            and int(row["lease_until"] or 0) > now
            and current in ready
            and city_id in ready[current]
        ):
            continue

        eligible = [player_id for player_id, city_ids in ready.items() if city_id in city_ids]
        if current in eligible:
            assigned = current
        elif eligible:
            assigned = min(eligible, key=lambda player_id: (load.get(player_id, 0), player_id))
            load[assigned] = load.get(assigned, 0) + 1
        else:
            assigned = ""

        db.execute(
            """UPDATE rumor_hunter_cities
               SET status=?,assigned_player_id=?,lease_token='',lease_until=0,updated_at=?
               WHERE cycle_id=? AND clan_id=? AND city_id=?""",
            ("queued" if assigned else "unassigned", assigned, now, cycle_id, clan_id, city_id),
        )


def rumor_hunter_state(
    player_id: str, clan_id: str, *, ready: bool | None = None,
    nickname: str = "", unlocked: list[str] | None = None,
    timezone_name: str = "", touch: bool = True
) -> dict:
    cycle_id = active_rumor_route_date()
    now = utc_now()
    known = rumor_hunter_known_map(cycle_id)

    with db_session() as db:
        rumor_hunter_seed(db, cycle_id, clan_id, now)
        if touch:
            existing = db.execute(
                """SELECT ready,unlocked_json,nickname,timezone
                   FROM rumor_hunter_presence
                   WHERE cycle_id=? AND clan_id=? AND player_id=?""",
                (cycle_id, clan_id, player_id),
            ).fetchone()

            existing_ready = bool(existing["ready"]) if existing else False
            ready_value = existing_ready if ready is None else bool(ready)

            if unlocked is None:
                try:
                    unlocked_value = json.loads(existing["unlocked_json"] or "[]") if existing else []
                except (TypeError, json.JSONDecodeError):
                    unlocked_value = []
            else:
                unlocked_value = unlocked

            nickname_value = str(nickname or "")[:120]
            timezone_value = str(timezone_name or "")[:80]
            if existing:
                nickname_value = nickname_value or str(existing["nickname"] or "")
                timezone_value = timezone_value or str(existing["timezone"] or "")

            db.execute(
                """INSERT INTO rumor_hunter_presence(
                   cycle_id,clan_id,player_id,nickname,ready,unlocked_json,timezone,last_seen,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(cycle_id,clan_id,player_id) DO UPDATE SET
                     nickname=excluded.nickname,ready=excluded.ready,
                     unlocked_json=excluded.unlocked_json,timezone=excluded.timezone,
                     last_seen=excluded.last_seen,updated_at=excluded.updated_at""",
                (
                    cycle_id, clan_id, player_id, nickname_value, int(ready_value),
                    json.dumps(rumor_hunter_unlocked(unlocked_value), separators=(",", ":")),
                    timezone_value, now, now,
                ),
            )

        rumor_hunter_rebalance(db, cycle_id, clan_id, known, now)

        city_rows = db.execute(
            "SELECT * FROM rumor_hunter_cities WHERE cycle_id=? AND clan_id=? ORDER BY city_order",
            (cycle_id, clan_id),
        ).fetchall()
        players = db.execute(
            """SELECT player_id,nickname,ready,unlocked_json,last_seen
               FROM rumor_hunter_presence
               WHERE cycle_id=? AND clan_id=? AND last_seen>=?
               ORDER BY ready DESC,last_seen DESC""",
            (cycle_id, clan_id, now - RUMOR_HUNTER_PRESENCE_SECONDS),
        ).fetchall()
        history = db.execute(
            """SELECT player_id,city_id,event,detail_json,created_at
               FROM rumor_hunter_history
               WHERE cycle_id=? AND clan_id=? ORDER BY id DESC LIMIT 60""",
            (cycle_id, clan_id),
        ).fetchall()

    cities = []
    for row in city_rows:
        city_id = str(row["city_id"])
        points = (known.get(city_id) or {}).get("points") or []
        if not points:
            try:
                points = json.loads(row["jackpots_json"] or "[]")
            except (TypeError, json.JSONDecodeError):
                points = []
        cities.append({
            "city_id": city_id,
            "city_key": row["city_key"],
            "name": row["city_name"],
            "order": row["city_order"],
            "status": row["status"],
            "assigned_player_id": row["assigned_player_id"],
            "lease_until": row["lease_until"],
            "probes": row["probes"],
            "posts": row["posts"],
            "wait409": row["wait409"],
            "jackpots": points[:3],
            "updated_at": row["updated_at"],
            "completed_at": row["completed_at"],
        })

    people = []
    for row in players:
        try:
            unlocked_rows = json.loads(row["unlocked_json"] or "[]")
        except (TypeError, json.JSONDecodeError):
            unlocked_rows = []
        people.append({
            "player_id": row["player_id"],
            "nickname": row["nickname"],
            "ready": bool(row["ready"]),
            "unlocked_city_ids": unlocked_rows,
            "last_seen": row["last_seen"],
        })

    events = []
    for row in history:
        try:
            detail = json.loads(row["detail_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            detail = {}
        events.append({
            "player_id": row["player_id"],
            "city_id": row["city_id"],
            "event": row["event"],
            "detail": detail,
            "created_at": row["created_at"],
        })

    mine = [
        row["city_id"] for row in cities
        if row["status"] in ("queued", "running")
        and str(row["assigned_player_id"]) == str(player_id)
    ]
    done = sum(1 for row in cities if row["status"] == "done" and len(row["jackpots"]) >= 3)
    phase = "complete" if done >= 17 else ("running" if any(row["ready"] for row in people) else "prep")
    return {
        "ok": True,
        "revision": HK_RUMORS_COORDINATOR_R3,
        "cycle_id": cycle_id,
        "clan_id": clan_id,
        "self_player_id": player_id,
        "phase": phase,
        "cities": cities,
        "players": people,
        "self_search_city_ids": mine,
        "complete": done,
        "total": 17,
        "history": events,
        "source": "kokkaras+hk",
        "server_time": now,
    }


def rumor_hunter_lease_token(player_id: str, city_id: str) -> str:
    raw = f"{player_id}|{city_id}|{utc_now()}|{os.urandom(18).hex()}".encode()
    return hashlib.sha256(raw).hexdigest()[:48]


def rumor_hunter_action(player_id: str, action: str, payload: dict) -> dict:
    action = str(action or "").strip().lower()
    clan_id = rumor_hunter_id(payload.get("clan_id"), "clan id")
    nickname = str(payload.get("nickname") or "")[:120]
    timezone_name = str(payload.get("timezone") or "")[:80]
    unlocked = rumor_hunter_unlocked(payload.get("unlocked_city_ids"))
    cycle_id = active_rumor_route_date()
    now = utc_now()

    if action in ("state", "heartbeat"):
        return rumor_hunter_state(
            player_id, clan_id,
            ready=None if action == "state" else bool(payload.get("ready")),
            nickname=nickname,
            unlocked=unlocked if payload.get("unlocked_city_ids") is not None else None,
            timezone_name=timezone_name,
            touch=True,
        )

    if action == "leave":
        with db_session() as db:
            owned = db.execute(
                """SELECT city_id FROM rumor_hunter_cities
                   WHERE cycle_id=? AND clan_id=? AND assigned_player_id=?
                     AND status IN ('queued','running')""",
                (cycle_id, clan_id, player_id),
            ).fetchall()
            db.execute(
                """UPDATE rumor_hunter_presence SET ready=0,last_seen=?,updated_at=?
                   WHERE cycle_id=? AND clan_id=? AND player_id=?""",
                (now, now, cycle_id, clan_id, player_id),
            )
            db.execute(
                """UPDATE rumor_hunter_cities
                   SET status='unassigned',assigned_player_id='',lease_token='',lease_until=0,updated_at=?
                   WHERE cycle_id=? AND clan_id=? AND assigned_player_id=?
                     AND status IN ('queued','running')""",
                (now, cycle_id, clan_id, player_id),
            )
            for row in owned:
                rumor_hunter_history_add(
                    db, cycle_id, clan_id, player_id, str(row["city_id"]), "leave", {}
                )
        return rumor_hunter_state(
            player_id, clan_id, ready=False, nickname=nickname,
            unlocked=unlocked, timezone_name=timezone_name, touch=True
        )

    city_id = rumor_hunter_id(payload.get("city_id"), "city id")
    if city_id not in RUMOR_HUNTER_CITY_IDS:
        raise ValueError("unknown rumor city")

    if action == "claim":
        state = rumor_hunter_state(
            player_id, clan_id, ready=True, nickname=nickname,
            unlocked=unlocked, timezone_name=timezone_name, touch=True
        )
        city = next((row for row in state["cities"] if row["city_id"] == city_id), None)
        if city and city["status"] == "done" and len(city["jackpots"]) >= 3:
            return {"ok": False, "error": "RESULT_READY", "state": state}

        db = connect()
        token = ""
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                """SELECT status,assigned_player_id,lease_until
                   FROM rumor_hunter_cities WHERE cycle_id=? AND clan_id=? AND city_id=?""",
                (cycle_id, clan_id, city_id),
            ).fetchone()
            if not row or str(row["assigned_player_id"] or "") != str(player_id):
                db.rollback()
                return {"ok": False, "error": "NOT_ASSIGNED", "state": state}
            if str(row["status"]) == "running" and int(row["lease_until"] or 0) > now:
                db.rollback()
                return {"ok": False, "error": "GLOBAL_BUSY", "state": state}

            token = rumor_hunter_lease_token(player_id, city_id)
            db.execute(
                """UPDATE rumor_hunter_cities
                   SET status='running',lease_token=?,lease_until=?,
                       probes=0,posts=0,wait409=0,jackpots_json='[]',updated_at=?
                   WHERE cycle_id=? AND clan_id=? AND city_id=?""",
                (token, now + RUMOR_HUNTER_LEASE_SECONDS, now, cycle_id, clan_id, city_id),
            )
            rumor_hunter_history_add(db, cycle_id, clan_id, player_id, city_id, "claim", {})
            db.commit()
        finally:
            db.close()
        return {
            "ok": True,
            "lease_token": token,
            "lease_until": now + RUMOR_HUNTER_LEASE_SECONDS,
            "state": rumor_hunter_state(player_id, clan_id, touch=False),
        }

    lease_token = str(payload.get("lease_token") or "")

    if action in ("progress", "mark_open"):
        fresh_state = rumor_hunter_state(player_id, clan_id, touch=False)
        fresh_city = next((row for row in fresh_state["cities"] if row["city_id"] == city_id), None)
        if fresh_city and fresh_city["status"] == "done" and len(fresh_city["jackpots"]) >= 3:
            return {"ok": False, "error": "RESULT_READY", "state": fresh_state}

        try:
            probes = max(0, min(10000, int(payload.get("probes") or 0)))
            posts = max(0, min(10000, int(payload.get("posts") or 0)))
            wait409 = max(0, min(10000, int(payload.get("wait409") or 0)))
        except (TypeError, ValueError):
            probes = posts = wait409 = 0
        jackpots = payload.get("jackpots") if isinstance(payload.get("jackpots"), list) else []

        lease_ok = False
        with db_session() as db:
            row = db.execute(
                """SELECT assigned_player_id,lease_token,status FROM rumor_hunter_cities
                   WHERE cycle_id=? AND clan_id=? AND city_id=?""",
                (cycle_id, clan_id, city_id),
            ).fetchone()
            lease_ok = bool(
                row
                and str(row["assigned_player_id"] or "") == str(player_id)
                and str(row["lease_token"] or "") == lease_token
                and str(row["status"]) == "running"
            )
            if lease_ok:
                db.execute(
                    """UPDATE rumor_hunter_cities
                       SET lease_until=?,probes=?,posts=?,wait409=?,jackpots_json=?,updated_at=?
                       WHERE cycle_id=? AND clan_id=? AND city_id=?""",
                    (
                        now + RUMOR_HUNTER_LEASE_SECONDS,
                        probes, posts, wait409,
                        json.dumps(jackpots[:3], ensure_ascii=False, separators=(",", ":"))[:12000],
                        now, cycle_id, clan_id, city_id,
                    ),
                )
                if action == "mark_open":
                    rumor_hunter_history_add(
                        db, cycle_id, clan_id, player_id, city_id, "open",
                        {"probes": probes, "posts": posts}
                    )

        state = rumor_hunter_state(player_id, clan_id, touch=False)
        return {"ok": lease_ok, **({} if lease_ok else {"error": "LEASE_LOST"}), "state": state}

    if action == "done":
        raw_points = payload.get("jackpots")
        if not isinstance(raw_points, list) or len(raw_points) < 3:
            raise ValueError("three jackpot points required")

        points = []
        seen = set()
        for point in raw_points:
            if not isinstance(point, dict):
                continue
            gamearea_id = rumor_hunter_id(point.get("gamearea_id"), "gamearea id")
            try:
                x, y = int(point.get("x")), int(point.get("y"))
            except (TypeError, ValueError) as error:
                raise ValueError("invalid jackpot coordinates") from error
            if not (-500 <= x <= 500 and -500 <= y <= 500):
                raise ValueError("jackpot coordinates out of range")
            if gamearea_id in seen:
                continue
            seen.add(gamearea_id)
            rumor_id = str(point.get("rumor_id") or "rumor_jackpot_hunter")[:160]
            if "jackpot" not in rumor_id.casefold():
                rumor_id = "rumor_jackpot_hunter"
            points.append({
                "x": x, "y": y, "gamearea_id": gamearea_id,
                "rumor_id": rumor_id, "source": "hk-hunter",
            })
            if len(points) >= 3:
                break
        if len(points) != 3:
            raise ValueError("three unique jackpot points required")

        db = connect()
        completed = False
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                """SELECT assigned_player_id,lease_token,status FROM rumor_hunter_cities
                   WHERE cycle_id=? AND clan_id=? AND city_id=?""",
                (cycle_id, clan_id, city_id),
            ).fetchone()
            completed = bool(
                row
                and str(row["assigned_player_id"] or "") == str(player_id)
                and str(row["lease_token"] or "") == lease_token
                and str(row["status"]) == "running"
            )
            if not completed:
                db.rollback()
            else:
                meta = RUMOR_HUNTER_CITY_META[city_id]
                for point in points:
                    db.execute(
                        """INSERT INTO rumor_observations(
                           route_date,city_id,city_key,city_name,x,y,gamearea_id,
                           rumor_id,source,observed_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?)
                           ON CONFLICT(route_date,city_id,gamearea_id) DO UPDATE SET
                             x=excluded.x,y=excluded.y,rumor_id=excluded.rumor_id,
                             source=excluded.source,
                             observed_at=MAX(rumor_observations.observed_at,excluded.observed_at)""",
                        (
                            cycle_id, city_id, meta["city_key"], meta["city_name"],
                            point["x"], point["y"], point["gamearea_id"],
                            point["rumor_id"], "hk-hunter", now,
                        ),
                    )
                db.execute(
                    """UPDATE rumor_hunter_cities
                       SET status='done',assigned_player_id='',lease_token='',lease_until=0,
                           jackpots_json=?,completed_at=?,updated_at=?
                       WHERE cycle_id=? AND clan_id=? AND city_id=?""",
                    (
                        json.dumps(points, ensure_ascii=False, separators=(",", ":")),
                        now, now, cycle_id, clan_id, city_id,
                    ),
                )
                rumor_hunter_history_add(
                    db, cycle_id, clan_id, player_id, city_id, "done",
                    {"jackpots": points}
                )
                db.commit()
        finally:
            db.close()

        state = rumor_hunter_state(player_id, clan_id, touch=False)
        return {"ok": completed, **({} if completed else {"error": "LEASE_LOST"}), "state": state}

    if action in ("release", "block_release"):
        released = False
        with db_session() as db:
            row = db.execute(
                """SELECT assigned_player_id,lease_token FROM rumor_hunter_cities
                   WHERE cycle_id=? AND clan_id=? AND city_id=?""",
                (cycle_id, clan_id, city_id),
            ).fetchone()
            released = bool(
                row
                and str(row["assigned_player_id"] or "") == str(player_id)
                and (not lease_token or str(row["lease_token"] or "") == lease_token)
            )
            if released:
                db.execute(
                    """UPDATE rumor_hunter_cities
                       SET status='queued',lease_token='',lease_until=0,updated_at=?
                       WHERE cycle_id=? AND clan_id=? AND city_id=?""",
                    (now, cycle_id, clan_id, city_id),
                )
                rumor_hunter_history_add(
                    db, cycle_id, clan_id, player_id, city_id, action, {}
                )
        return {
            "ok": released,
            **({} if released else {"error": "LEASE_LOST"}),
            "state": rumor_hunter_state(player_id, clan_id, touch=False),
        }

    raise ValueError("unknown rumor hunter action")


'''
s = s.replace(helper_anchor, module + helper_anchor, 1)

route_anchor = '''            elif path == "/api/v1/rumors/report":
                origin = self.headers.get("Origin", "")
'''
need(route_anchor, "rumor report route")
route = '''            elif path == "/api/v1/rumors/hunter":
                origin = self.headers.get("Origin", "")
                if origin not in ALLOWED_ORIGINS:
                    self.send_json(HTTPStatus.FORBIDDEN, {"error":"origin_not_allowed"}); return
                player_id = self.recipe_player()
                if not player_id:
                    self.send_json(HTTPStatus.UNAUTHORIZED, {"error":"unauthorized"}); return
                body = self.read_json()
                if not isinstance(body, dict):
                    self.send_json(HTTPStatus.BAD_REQUEST, {"error":"bad_request"}); return
                try:
                    result = rumor_hunter_action(
                        str(player_id), str(body.get("action") or ""), body
                    )
                except ValueError as error:
                    self.send_json(
                        HTTPStatus.BAD_REQUEST,
                        {"error":"bad_rumor_hunter_request","detail":str(error)}
                    ); return
                self.send_json(HTTPStatus.OK, result)
'''
s = s.replace(route_anchor, route + route_anchor, 1)

for marker in (
    "HK_RUMORS_COORDINATOR_R3",
    "CREATE TABLE IF NOT EXISTS rumor_hunter_presence",
    "CREATE TABLE IF NOT EXISTS rumor_hunter_cities",
    "CREATE TABLE IF NOT EXISTS rumor_hunter_history",
    "def rumor_hunter_action",
    'path == "/api/v1/rumors/hunter"',
    "RUMOR_HUNTER_LEASE_SECONDS = 90",
    "RESULT_READY",
):
    if marker not in s:
        raise SystemExit("missing marker: " + marker)

target.write_text(s, encoding="utf-8")
print("RUMORS_COORDINATOR_R3_PATCH=PASS")
