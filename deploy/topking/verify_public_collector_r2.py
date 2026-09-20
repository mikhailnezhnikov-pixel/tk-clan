#!/usr/bin/env python3
import json, sqlite3
DB="/var/lib/hamsterking-license/licenses.db"
db=sqlite3.connect(DB)
try:
    war=db.execute("select snapshot_json,source_player_id,updated_at from public_clan_war_snapshot where singleton=1").fetchone()
    assert war, "war snapshot missing"
    doc=json.loads(war[0])
    assert doc.get("opponent"), doc
    assert war[1]=="server-collector", war[1]
    print("war_opponent="+str(doc.get("opponent")))
    print("war_source="+str(war[1]))
    print("war_updated_at="+str(war[2]))
    for kind in ("alliance_defense","alliance_influence","alliance_power"):
        count,source,updated=db.execute(
            "select count(*),min(source_player_id),max(updated_at) from public_rating_snapshots where kind=?",
            (kind,)
        ).fetchone()
        print(f"{kind}_count={count}")
        print(f"{kind}_source={source}")
        print(f"{kind}_updated_at={updated}")
        assert count>0, kind
        assert source=="server-collector", (kind,source)
    for kind in ("alliance_defense","alliance_influence","alliance_power"):
        rows=db.execute(
            "select rank,name,value from public_rating_snapshots where kind=? order by rank limit 5",
            (kind,)
        ).fetchall()
        print("top_"+kind+"="+json.dumps(rows,ensure_ascii=False))
finally:
    db.close()
