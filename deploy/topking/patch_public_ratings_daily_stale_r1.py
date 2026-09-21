from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="PUBLIC_RATINGS_DAILY_STALE_R1"
if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)

old='''    return {"ok": True, "kind": kind, "updated_at": updated_at,
            "stale": bool(updated_at and updated_at < utc_now() - 1800),
            "rows": [{"rank": row["rank"], "name": row["name"], "value": row["value"]} for row in rows]}
'''
new='''    # PUBLIC_RATINGS_DAILY_STALE_R1
    # Ratings are collected daily. Keep a 12-hour grace window so a delayed
    # daily run is not mislabeled as stale, while a missed full cycle is.
    ratings_stale_seconds = 36 * 60 * 60
    return {"ok": True, "kind": kind, "updated_at": updated_at,
            "stale": bool(updated_at and updated_at < utc_now() - ratings_stale_seconds),
            "rows": [{"rank": row["rank"], "name": row["name"], "value": row["value"]} for row in rows]}
'''
if s.count(old)!=1:
    raise SystemExit(f"ratings stale anchor count={s.count(old)}")
s=s.replace(old,new,1)
path.write_text(s)
print(MARKER+"_PATCH_OK")
