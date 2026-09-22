import sqlite3
db=sqlite3.connect("/var/lib/hamsterking-license/licenses.db"); db.row_factory=sqlite3.Row
ids=['1083594259','275051195','5112494832','5195339821','5225915725','5262908393','566546686']
for pid in ids:
    r=db.execute("SELECT player_id,note,active FROM licenses WHERE player_id=?",(pid,)).fetchone()
    print(pid, dict(r) if r else None)
