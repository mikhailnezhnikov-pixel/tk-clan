from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text(encoding="utf-8")
MARKER="TREASURE_GUIDE_CAPTURE_V1"

if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)

handler_anchor="class Handler"
if handler_anchor not in s:
    raise SystemExit("Handler class anchor missing")

helper=r'''
# TREASURE_GUIDE_CAPTURE_V1
def ensure_treasure_guide_capture_schema() -> None:
    with db_session() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS treasure_guide_captures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            capture_key TEXT NOT NULL UNIQUE,
            player_id TEXT NOT NULL,
            source TEXT NOT NULL,
            path TEXT NOT NULL DEFAULT '',
            payload_json TEXT NOT NULL DEFAULT '',
            page_text TEXT NOT NULL DEFAULT '',
            assets_json TEXT NOT NULL DEFAULT '[]',
            captured_at INTEGER NOT NULL
        )""")
        db.execute("""CREATE INDEX IF NOT EXISTS idx_treasure_guide_captures_at
                      ON treasure_guide_captures(captured_at DESC)""")


def accept_treasure_guide_capture(player_id: str, body: dict) -> dict:
    ensure_treasure_guide_capture_schema()
    capture_key=str(body.get("capture_key") or "").strip()[:160]
    source=str(body.get("source") or "").strip()[:40]
    path_value=str(body.get("path") or "").strip()[:260]
    payload_json=str(body.get("payload_json") or "")
    page_text=str(body.get("page_text") or "")
    assets=body.get("assets")
    if not capture_key or source not in ("api","dom"):
        raise ValueError("invalid treasure capture")
    if len(payload_json)>260_000 or len(page_text)>40_000:
        raise ValueError("treasure capture too large")
    if not isinstance(assets,list):
        assets=[]
    clean_assets=[]
    for value in assets[:220]:
        url=str(value or "").strip()
        if not url or len(url)>1000:
            continue
        if not (url.startswith("https://") or url.startswith("http://")):
            continue
        clean_assets.append(url)
    now=utc_now()
    with db_session() as db:
        db.execute("""INSERT INTO treasure_guide_captures(
                        capture_key,player_id,source,path,payload_json,page_text,assets_json,captured_at)
                      VALUES(?,?,?,?,?,?,?,?)
                      ON CONFLICT(capture_key) DO UPDATE SET
                        player_id=excluded.player_id,
                        source=excluded.source,
                        path=excluded.path,
                        payload_json=CASE WHEN excluded.payload_json<>'' THEN excluded.payload_json ELSE treasure_guide_captures.payload_json END,
                        page_text=CASE WHEN excluded.page_text<>'' THEN excluded.page_text ELSE treasure_guide_captures.page_text END,
                        assets_json=CASE WHEN excluded.assets_json<>'[]' THEN excluded.assets_json ELSE treasure_guide_captures.assets_json END,
                        captured_at=excluded.captured_at""",
                   (capture_key,str(player_id),source,path_value,payload_json,page_text,
                    json.dumps(clean_assets,ensure_ascii=False,separators=(",",":")),now))
    return {"ok":True,"capture_key":capture_key,"assets":len(clean_assets)}


'''
s=s.replace(handler_anchor,helper+handler_anchor,1)

post_anchor='''            elif path == "/api/v1/public-collector/auth-sync":
'''
post_route='''            elif path == "/api/v1/treasure-guide/capture":
                origin = self.headers.get("Origin", "")
                if origin not in ALLOWED_ORIGINS:
                    self.send_json(HTTPStatus.FORBIDDEN, {"error": "origin_not_allowed"}); return
                player_id = self.recipe_player()
                if not player_id:
                    self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"}); return
                if not rate_allowed(f"treasure-guide-capture:{player_id}", 180, 600):
                    self.send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "rate_limited"}); return
                try:
                    result = accept_treasure_guide_capture(player_id, self.read_json(360_000))
                except ValueError:
                    self.send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_treasure_capture"}); return
                self.send_json(HTTPStatus.OK, result)
            elif path == "/api/v1/public-collector/auth-sync":
'''
if post_anchor not in s:
    raise SystemExit("POST insertion anchor missing")
s=s.replace(post_anchor,post_route,1)

path.write_text(s,encoding="utf-8")
print("TREASURE_GUIDE_CAPTURE_V1_PATCH_OK")
