from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text(encoding="utf-8")
MARKER="PUBLIC_COLLECTOR_ACTIVITY_LEASE_R1"

if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)

required=[
    "PUBLIC_COLLECTOR_AUTH_HEARTBEAT_R1",
    "PUBLIC_COLLECTOR_AUTH_LOCK = threading.Lock()",
    "def public_collector_auth_sync_allowed(player_id: str) -> bool:",
    "def _public_collector_write_private(target: str, text: str) -> None:",
    'elif path == "/api/v1/public-collector/auth-sync":',
    'elif path == "/api/v1/public-snapshot":',
]
for marker in required:
    if marker not in s:
        raise SystemExit("missing server marker: "+marker)

const_anchor="PUBLIC_COLLECTOR_AUTH_LOCK = threading.Lock()\n"
const_block=const_anchor+'''# PUBLIC_COLLECTOR_ACTIVITY_LEASE_R1
PUBLIC_COLLECTOR_ACTIVITY_PATH = os.environ.get(
    "HK_PUBLIC_COLLECTOR_ACTIVITY_FILE",
    "/var/lib/hamsterking-license/public-collector-activity.json",
)
PUBLIC_COLLECTOR_ACTIVITY_LOCK = threading.Lock()
'''
if s.count(const_anchor)!=1:
    raise SystemExit(f"activity const anchor count={s.count(const_anchor)}")
s=s.replace(const_anchor,const_block,1)

helper_anchor="def license_check(player_id: str, device_id: str, version: str, client_ip: str = \"\") -> tuple[int, dict]:\n"
if s.count(helper_anchor)!=1:
    raise SystemExit(f"license anchor count={s.count(helper_anchor)}")

helpers=r'''
def public_collector_activity_lease(player_id: str, document: object) -> dict:
    if not public_collector_auth_sync_allowed(player_id):
        raise PermissionError("collector identity not allowed")
    if not isinstance(document, dict):
        raise ValueError("activity object required")
    active = bool(document.get("active"))
    reason = re.sub(r"\s+", " ", str(document.get("reason") or "")).strip()[:120]
    now = utc_now()
    player_hash = _public_collector_identity_digest(player_id)
    with PUBLIC_COLLECTOR_ACTIVITY_LOCK:
        if active:
            try:
                ttl = int(document.get("ttl_seconds") or 90)
            except (TypeError, ValueError):
                ttl = 90
            ttl = max(30, min(ttl, 180))
            lease_until = now + ttl
            payload = {
                "active": True,
                "player_sha256": player_hash,
                "lease_until": lease_until,
                "updated_at": now,
                "reason": reason,
            }
            _public_collector_write_private(
                PUBLIC_COLLECTOR_ACTIVITY_PATH,
                json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
            )
            return {"ok": True, "active": True, "lease_until": lease_until, "ttl_seconds": ttl}
        try:
            current = json.loads(Path(PUBLIC_COLLECTOR_ACTIVITY_PATH).read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            current = {}
        if current and str(current.get("player_sha256") or "") not in ("", player_hash):
            raise PermissionError("collector activity owner mismatch")
        try:
            Path(PUBLIC_COLLECTOR_ACTIVITY_PATH).unlink()
        except FileNotFoundError:
            pass
        return {"ok": True, "active": False, "lease_until": 0, "ttl_seconds": 0}


'''
s=s.replace(helper_anchor,helpers+helper_anchor,1)

route_start=s.index('            elif path == "/api/v1/public-collector/auth-sync":')
route_next=s.index('            elif path == "/api/v1/public-snapshot":',route_start)
activity_route=r'''            elif path == "/api/v1/public-collector/activity":
                origin = self.headers.get("Origin", "")
                if origin not in ALLOWED_ORIGINS:
                    self.send_json(HTTPStatus.FORBIDDEN, {"error": "origin_not_allowed"}); return
                player_id = self.recipe_player()
                if not player_id:
                    self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"}); return
                if not public_collector_auth_sync_allowed(player_id):
                    self.send_json(HTTPStatus.FORBIDDEN, {"error": "collector_identity_not_allowed"}); return
                if not rate_allowed(f"public-collector-activity:{player_id}", 120, 900):
                    self.send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "rate_limited"}); return
                try:
                    result = public_collector_activity_lease(player_id, self.read_json(4096))
                except PermissionError:
                    self.send_json(HTTPStatus.FORBIDDEN, {"error": "collector_activity_rejected"}); return
                except ValueError:
                    self.send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_collector_activity"}); return
                self.send_json(HTTPStatus.OK, result)
'''
s=s[:route_next]+activity_route+s[route_next:]

for marker in [
    MARKER,
    "PUBLIC_COLLECTOR_ACTIVITY_PATH",
    "PUBLIC_COLLECTOR_ACTIVITY_LOCK",
    "def public_collector_activity_lease(",
    'path == "/api/v1/public-collector/activity"',
    'public-collector-activity:{player_id}',
    '"ttl_seconds": ttl',
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

path.write_text(s,encoding="utf-8")
print("PUBLIC_COLLECTOR_ACTIVITY_LEASE_R1_PATCH=PASS")
