from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text(encoding="utf-8")
MARKER="RUNTIME_SMOKE_CAPTURE_V1"

if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)

handler_anchor="class Handler"
if handler_anchor not in s:
    raise SystemExit("Handler class anchor missing")

helper=r'''
# RUNTIME_SMOKE_CAPTURE_V1
def ensure_runtime_smoke_capture_schema() -> None:
    with db_session() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS runtime_smoke_captures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_key TEXT NOT NULL,
            capture_key TEXT NOT NULL,
            script_version TEXT NOT NULL DEFAULT '',
            revision TEXT NOT NULL DEFAULT '',
            summary_json TEXT NOT NULL DEFAULT '{}',
            events_json TEXT NOT NULL DEFAULT '[]',
            captured_at INTEGER NOT NULL,
            UNIQUE(player_key,capture_key)
        )""")
        db.execute("""CREATE INDEX IF NOT EXISTS idx_runtime_smoke_captures_at
                      ON runtime_smoke_captures(captured_at DESC)""")


def runtime_smoke_clean(value, depth: int = 0):
    if depth > 6:
        return None
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[:1200]
    if isinstance(value, list):
        return [runtime_smoke_clean(item, depth + 1) for item in value[:160]]
    if isinstance(value, dict):
        result = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= 80:
                break
            name = str(key)[:100]
            result[name] = runtime_smoke_clean(item, depth + 1)
        return result
    return str(value)[:1200]


def accept_runtime_smoke_capture(player_id: str, body: dict) -> dict:
    ensure_runtime_smoke_capture_schema()
    capture_key=str(body.get("capture_key") or "").strip()[:160]
    script_version=str(body.get("script_version") or "").strip()[:64]
    revision=str(body.get("revision") or "").strip()[:100]
    summary=body.get("summary")
    events=body.get("events")
    if not capture_key or not isinstance(summary, dict) or not isinstance(events, list):
        raise ValueError("invalid runtime smoke capture")

    clean_events=[]
    for event in events[:160]:
        if not isinstance(event, dict):
            continue
        event_type=str(event.get("type") or "")[:120]
        if not event_type.startswith("runtime-smoke-"):
            continue
        clean_events.append({
            "at":str(event.get("at") or "")[:80],
            "type":event_type,
            "data":runtime_smoke_clean(event.get("data") if isinstance(event.get("data"), dict) else {})
        })

    clean_summary=runtime_smoke_clean(summary)
    summary_json=json.dumps(clean_summary,ensure_ascii=False,separators=(",",":"))
    events_json=json.dumps(clean_events,ensure_ascii=False,separators=(",",":"))
    if len(summary_json)>40_000 or len(events_json)>140_000:
        raise ValueError("runtime smoke capture too large")

    player_key=contributor_id(str(player_id))
    now=utc_now()
    with db_session() as db:
        db.execute("""INSERT INTO runtime_smoke_captures(
                        player_key,capture_key,script_version,revision,summary_json,events_json,captured_at)
                      VALUES(?,?,?,?,?,?,?)
                      ON CONFLICT(player_key,capture_key) DO UPDATE SET
                        script_version=excluded.script_version,
                        revision=excluded.revision,
                        summary_json=excluded.summary_json,
                        events_json=excluded.events_json,
                        captured_at=excluded.captured_at""",
                   (player_key,capture_key,script_version,revision,summary_json,events_json,now))
    return {"ok":True,"events":len(clean_events),"captured_at":now}


'''
s=s.replace(handler_anchor,helper+handler_anchor,1)

post_anchor='''            elif path == "/api/v1/treasure-guide/capture":
'''
post_route='''            elif path == "/api/v1/runtime-smoke/capture":
                origin = self.headers.get("Origin", "")
                if origin not in ALLOWED_ORIGINS:
                    self.send_json(HTTPStatus.FORBIDDEN, {"error": "origin_not_allowed"}); return
                player_id = self.recipe_player()
                if not player_id:
                    self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"}); return
                if not rate_allowed(f"runtime-smoke-capture:{player_id}", 120, 600):
                    self.send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "rate_limited"}); return
                try:
                    result = accept_runtime_smoke_capture(player_id, self.read_json(220_000))
                except ValueError:
                    self.send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_runtime_smoke_capture"}); return
                self.send_json(HTTPStatus.OK, result)
            elif path == "/api/v1/treasure-guide/capture":
'''
if post_anchor not in s:
    raise SystemExit("POST insertion anchor missing")
s=s.replace(post_anchor,post_route,1)

path.write_text(s,encoding="utf-8")
print("RUNTIME_SMOKE_CAPTURE_V1_PATCH_OK")
