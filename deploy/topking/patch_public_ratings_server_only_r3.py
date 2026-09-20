from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="PUBLIC_RATINGS_SERVER_ONLY_R3"
if MARKER in s:
    print("PUBLIC_RATINGS_SERVER_ONLY_R3_ALREADY_PRESENT")
    raise SystemExit(0)

old='''        rows = db.execute("""SELECT rank,name,value,updated_at FROM public_rating_snapshots
                             WHERE kind=? ORDER BY rank LIMIT 100""", (kind,)).fetchall()
'''
new='''        # PUBLIC_RATINGS_SERVER_ONLY_R3
        rows = db.execute("""SELECT rank,name,value,updated_at FROM public_rating_snapshots
                             WHERE kind=? AND source_player_id='server-collector'
                             ORDER BY rank LIMIT 100""", (kind,)).fetchall()
'''
if s.count(old)!=1:
    raise SystemExit(f"public_ratings anchor count={s.count(old)}")
s=s.replace(old,new,1)
path.write_text(s)
print("PUBLIC_RATINGS_SERVER_ONLY_R3_PATCH_OK")
