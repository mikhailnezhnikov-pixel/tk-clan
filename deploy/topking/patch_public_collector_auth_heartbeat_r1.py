from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="PUBLIC_COLLECTOR_AUTH_HEARTBEAT_R1"
if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)

const_anchor='PUBLIC_BASE = os.environ.get("HK_PUBLIC_BASE", "https://hk-license.89.125.1.71.sslip.io").rstrip("/")\n'
if s.count(const_anchor)!=1:
    raise SystemExit(f"const anchor count={s.count(const_anchor)}")
const_block=const_anchor+'''# PUBLIC_COLLECTOR_AUTH_HEARTBEAT_R1
PUBLIC_COLLECTOR_IDENTITY_PATH = os.environ.get(
    "HK_PUBLIC_COLLECTOR_IDENTITY_FILE",
    "/var/lib/hamsterking-license/public-collector-identity.sha256",
)
PUBLIC_COLLECTOR_TOKEN_PATH = os.environ.get(
    "HK_PUBLIC_COLLECTOR_TOKEN_FILE",
    "/var/lib/hamsterking-license/public-collector-token",
)
PUBLIC_COLLECTOR_AUTH_BOOTSTRAP_PATH = os.environ.get(
    "HK_PUBLIC_COLLECTOR_AUTH_BOOTSTRAP",
    "/var/lib/hamsterking-license/public-collector-auth.json",
)
PUBLIC_COLLECTOR_GAME_API = os.environ.get(
    "HK_PUBLIC_COLLECTOR_GAME_API",
    "https://hk-game-api.hwgame.cloud",
).rstrip("/")
PUBLIC_COLLECTOR_AUTH_LOCK = threading.Lock()
'''
s=s.replace(const_anchor,const_block,1)

license_anchor='def license_check(player_id: str, device_id: str, version: str, client_ip: str = "") -> tuple[int, dict]:\n'
if s.count(license_anchor)!=1:
    raise SystemExit(f"license anchor count={s.count(license_anchor)}")
helpers=r'''
def _public_collector_identity_digest(player_id: str) -> str:
    return hashlib.sha256(str(player_id or "").strip().encode("utf-8")).hexdigest()


def public_collector_auth_sync_allowed(player_id: str) -> bool:
    try:
        with open(PUBLIC_COLLECTOR_IDENTITY_PATH, "r", encoding="ascii") as source:
            expected = source.read(256).strip()
    except OSError:
        return False
    actual = _public_collector_identity_digest(player_id)
    return bool(expected and actual and hmac.compare_digest(expected, actual))


def _public_collector_write_private(target: str, text: str) -> None:
    directory = os.path.dirname(target)
    if directory:
        os.makedirs(directory, exist_ok=True)
    tmp = target + ".tmp"
    with open(tmp, "w", encoding="utf-8") as output:
        output.write(text)
    os.chmod(tmp, 0o600)
    os.replace(tmp, target)


def _public_collector_game_player(token: str) -> str:
    token = str(token or "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token or len(token) > 8192:
        raise PermissionError("invalid game token")
    request = urllib.request.Request(
        PUBLIC_COLLECTOR_GAME_API + "/player/me",
        data=b"{}",
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "TopKing-Public-Auth-Sync/1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            document = json.loads(response.read(5_000_000).decode("utf-8-sig"))
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise PermissionError("game token rejected") from exc
        raise OSError("game auth validation failed") from exc
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise OSError("game auth validation failed") from exc
    player = document.get("player") if isinstance(document, dict) and isinstance(document.get("player"), dict) else document
    if not isinstance(player, dict):
        return ""
    for key in ("id", "player_id", "playerId", "uuid"):
        value = player.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def accept_public_collector_auth(player_id: str, document: object) -> dict:
    if not public_collector_auth_sync_allowed(player_id):
        raise PermissionError("collector identity not allowed")
    if not isinstance(document, dict):
        raise ValueError("auth object required")
    token = str(document.get("game_token") or "").strip()
    auth_type = str(document.get("auth_type") or "").strip()
    auth_data = str(document.get("auth_data") or "")
    platform = str(document.get("platform") or "").strip()
    if not token or len(token) > 8192:
        raise ValueError("invalid game token")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", auth_type):
        raise ValueError("invalid auth type")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,16}", platform):
        raise ValueError("invalid platform")
    if not auth_data or len(auth_data) > 50_000:
        raise ValueError("invalid auth data")
    candidate_player = _public_collector_game_player(token)
    if not candidate_player or candidate_player != player_id:
        raise PermissionError("collector player mismatch")
    if not public_collector_auth_sync_allowed(candidate_player):
        raise PermissionError("collector identity mismatch")
    bootstrap = {
        "auth_type": auth_type,
        "auth_data": auth_data,
        "platform": platform,
        "updated_at": utc_now(),
    }
    with PUBLIC_COLLECTOR_AUTH_LOCK:
        _public_collector_write_private(PUBLIC_COLLECTOR_TOKEN_PATH, token + "\n")
        _public_collector_write_private(
            PUBLIC_COLLECTOR_AUTH_BOOTSTRAP_PATH,
            json.dumps(bootstrap, ensure_ascii=False, separators=(",", ":")) + "\n",
        )
    return {"ok": True, "accepted": True, "updated_at": utc_now()}


'''
s=s.replace(license_anchor,helpers+license_anchor,1)

old_return='''        return HTTPStatus.OK, {"allowed": True, "player_id": player_id, "token": token,
                               "check_after": 300, "expires_at": license_row["expires_at"], "update": update}
'''
new_return='''        return HTTPStatus.OK, {"allowed": True, "player_id": player_id, "token": token,
                               "check_after": 300, "expires_at": license_row["expires_at"], "update": update,
                               "public_collector_auth_sync": public_collector_auth_sync_allowed(player_id)}
'''
if s.count(old_return)!=1:
    raise SystemExit(f"license return anchor count={s.count(old_return)}")
s=s.replace(old_return,new_return,1)

route_anchor='''            elif path == "/api/v1/public-snapshot":
                origin = self.headers.get("Origin", "")
'''
if s.count(route_anchor)!=1:
    raise SystemExit(f"route anchor count={s.count(route_anchor)}")
route='''            elif path == "/api/v1/public-collector/auth-sync":
                origin = self.headers.get("Origin", "")
                if origin not in ALLOWED_ORIGINS:
                    self.send_json(HTTPStatus.FORBIDDEN, {"error": "origin_not_allowed"}); return
                player_id = self.recipe_player()
                if not player_id:
                    self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"}); return
                if not public_collector_auth_sync_allowed(player_id):
                    self.send_json(HTTPStatus.FORBIDDEN, {"error": "collector_identity_not_allowed"}); return
                if not rate_allowed(f"public-collector-auth:{player_id}", 12, 900):
                    self.send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "rate_limited"}); return
                try:
                    result = accept_public_collector_auth(player_id, self.read_json(70_000))
                except PermissionError:
                    self.send_json(HTTPStatus.FORBIDDEN, {"error": "collector_auth_rejected"}); return
                except ValueError:
                    self.send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_collector_auth"}); return
                except OSError:
                    self.send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "game_auth_unavailable"}); return
                self.send_json(HTTPStatus.OK, result)
            elif path == "/api/v1/public-snapshot":
                origin = self.headers.get("Origin", "")
'''
s=s.replace(route_anchor,route,1)

assert MARKER in s
path.write_text(s)
print("PUBLIC_COLLECTOR_AUTH_HEARTBEAT_R1_PATCH_OK")
