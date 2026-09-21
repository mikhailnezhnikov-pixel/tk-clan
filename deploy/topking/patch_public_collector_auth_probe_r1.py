from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="PUBLIC_COLLECTOR_AUTH_PROBE_R1"
if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)

const_anchor='PUBLIC_COLLECTOR_AUTH_LOCK = threading.Lock()\n'
if s.count(const_anchor)!=1:
    raise SystemExit(f"const anchor count={s.count(const_anchor)}")
const_block=const_anchor+'''# PUBLIC_COLLECTOR_AUTH_PROBE_R1
PUBLIC_COLLECTOR_AUTH_PROBE_PATH = os.environ.get(
    "HK_PUBLIC_COLLECTOR_AUTH_PROBE",
    "/var/lib/hamsterking-license/public-collector-auth-probe.json",
)
'''
s=s.replace(const_anchor,const_block,1)

helper_anchor='def accept_public_collector_auth(player_id: str, document: object) -> dict:\n'
if s.count(helper_anchor)!=1:
    raise SystemExit(f"helper anchor count={s.count(helper_anchor)}")
helper=r'''
def accept_public_collector_auth_probe(player_id: str, document: object) -> dict:
    if not public_collector_auth_sync_allowed(player_id):
        raise PermissionError("collector identity not allowed")
    if not isinstance(document, dict):
        raise ValueError("probe object required")

    def clean_names(value, limit=64):
        result = []
        if not isinstance(value, list):
            return result
        for item in value[:limit]:
            name = str(item or "").strip()
            if not name or len(name) > 128:
                continue
            if any(ord(ch) < 32 for ch in name):
                continue
            result.append(name)
        return result

    def clean_shapes(value):
        result = {}
        if not isinstance(value, dict):
            return result
        for key, fields in list(value.items())[:64]:
            name = str(key or "").strip()
            if not name or len(name) > 128:
                continue
            result[name] = clean_names(fields, 24)
        return result

    probe = {
        "local_storage_keys": clean_names(document.get("local_storage_keys")),
        "session_storage_keys": clean_names(document.get("session_storage_keys")),
        "cookie_names": clean_names(document.get("cookie_names")),
        "indexed_db_names": clean_names(document.get("indexed_db_names")),
        "json_shapes": clean_shapes(document.get("json_shapes")),
        "telegram_webapp_present": bool(document.get("telegram_webapp_present")),
        "telegram_init_data_present": bool(document.get("telegram_init_data_present")),
        "observed_auth_create": bool(document.get("observed_auth_create")),
        "current_bearer_present": bool(document.get("current_bearer_present")),
        "updated_at": utc_now(),
    }
    with PUBLIC_COLLECTOR_AUTH_LOCK:
        _public_collector_write_private(
            PUBLIC_COLLECTOR_AUTH_PROBE_PATH,
            json.dumps(probe, ensure_ascii=False, separators=(",", ":")) + "\n",
        )
    return {"ok": True, "accepted": True, "updated_at": probe["updated_at"]}


'''
s=s.replace(helper_anchor,helper+helper_anchor,1)

route_anchor='''            elif path == "/api/v1/public-collector/auth-sync":
                origin = self.headers.get("Origin", "")
'''
if s.count(route_anchor)!=1:
    raise SystemExit(f"route anchor count={s.count(route_anchor)}")
route='''            elif path == "/api/v1/public-collector/auth-probe":
                origin = self.headers.get("Origin", "")
                if origin not in ALLOWED_ORIGINS:
                    self.send_json(HTTPStatus.FORBIDDEN, {"error": "origin_not_allowed"}); return
                player_id = self.recipe_player()
                if not player_id:
                    self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"}); return
                if not public_collector_auth_sync_allowed(player_id):
                    self.send_json(HTTPStatus.FORBIDDEN, {"error": "collector_identity_not_allowed"}); return
                if not rate_allowed(f"public-collector-auth-probe:{player_id}", 4, 900):
                    self.send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "rate_limited"}); return
                try:
                    result = accept_public_collector_auth_probe(player_id, self.read_json(20_000))
                except PermissionError:
                    self.send_json(HTTPStatus.FORBIDDEN, {"error": "collector_probe_rejected"}); return
                except ValueError:
                    self.send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_collector_probe"}); return
                self.send_json(HTTPStatus.OK, result)
            elif path == "/api/v1/public-collector/auth-sync":
                origin = self.headers.get("Origin", "")
'''
s=s.replace(route_anchor,route,1)

assert MARKER in s
path.write_text(s)
print("PUBLIC_COLLECTOR_AUTH_PROBE_R1_PATCH_OK")
