from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="PUBLIC_SNAPSHOT_SERVER_ONLY_R3"

if MARKER in s:
    print("PUBLIC_SNAPSHOT_SERVER_ONLY_R3_ALREADY_PRESENT")
    raise SystemExit(0)

old='''def store_public_snapshot(player_id: str, document: object) -> dict:
    if not public_snapshot_member(player_id):
        raise PermissionError("member not allowed")
    if not isinstance(document, dict):
        raise ValueError("snapshot object required")
'''
new='''def store_public_snapshot(player_id: str, document: object) -> dict:
    if not public_snapshot_member(player_id):
        raise PermissionError("member not allowed")
    # PUBLIC_SNAPSHOT_SERVER_ONLY_R3
    # Legacy clients may still POST /api/v1/public-snapshot. Keep the endpoint
    # compatible, but never allow player clients to mutate the public cache.
    # Wars/Ratings are written exclusively by the isolated server collector.
    return {"ok": True, "ignored": True, "source": "server-collector-only", "updated_at": utc_now()}

    if not isinstance(document, dict):
        raise ValueError("snapshot object required")
'''
if s.count(old)!=1:
    raise SystemExit(f"store_public_snapshot anchor count={s.count(old)}")
s=s.replace(old,new,1)

assert MARKER in s
path.write_text(s)
print("PUBLIC_SNAPSHOT_SERVER_ONLY_R3_PATCH_OK")
