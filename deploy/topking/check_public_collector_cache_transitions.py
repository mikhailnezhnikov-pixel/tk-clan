#!/usr/bin/env python3
import importlib.util
import json
import os
import sqlite3
import tempfile
import time

LIVE="/opt/hamsterking-license/public_collector.py"

def yes(v): return "yes" if bool(v) else "no"

spec=importlib.util.spec_from_file_location("hk_collector_state_test",LIVE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

print("cache_transition_revision=PUBLIC_COLLECTOR_CACHE_TRANSITIONS_R1")

with tempfile.TemporaryDirectory(prefix="hk-collector-cache-") as td:
    db_path=os.path.join(td,"test.db")
    db=sqlite3.connect(db_path)
    db.executescript("""
    CREATE TABLE public_clan_war_snapshot(
      singleton INTEGER PRIMARY KEY,
      snapshot_json TEXT NOT NULL,
      source_player_id TEXT NOT NULL,
      updated_at INTEGER NOT NULL
    );
    CREATE TABLE public_rating_snapshots(
      kind TEXT NOT NULL,
      rank INTEGER NOT NULL,
      name TEXT NOT NULL,
      value REAL NOT NULL,
      source_player_id TEXT NOT NULL,
      updated_at INTEGER NOT NULL,
      PRIMARY KEY(kind,rank)
    );
    """)
    db.commit()
    db.close()

    real_db=mod.DB_PATH
    mod.DB_PATH=db_path
    try:
        now=int(time.time())
        active={
            "our_clan":"Top King",
            "opponent":"Synthetic Opponent",
            "opponent_hp":500,
            "opponent_hp_max":1000,
            "status":"active",
            "ends_at":now+600,
        }

        saved,state=mod.store_snapshot(True,active,{})
        db=sqlite3.connect(db_path)
        row=db.execute("SELECT snapshot_json,source_player_id,updated_at FROM public_clan_war_snapshot WHERE singleton=1").fetchone()
        db.close()
        active_written=bool(row and row[1]==mod.SOURCE and json.loads(row[0]).get("opponent")=="Synthetic Opponent")
        original_updated=int(row[2]) if row else 0
        print("active_war_written="+yes(active_written))
        print("active_war_state="+str(state))

        saved,state=mod.store_snapshot(True,None,{})
        db=sqlite3.connect(db_path)
        row2=db.execute("SELECT snapshot_json,source_player_id,updated_at FROM public_clan_war_snapshot WHERE singleton=1").fetchone()
        db.close()
        preserved=bool(row2 and row2[1]==mod.SOURCE and int(row2[2])==original_updated)
        print("empty_read_preserves_unexpired="+yes(preserved))
        print("empty_read_unexpired_state="+str(state))

        saved,state=mod.store_snapshot(False,None,{})
        db=sqlite3.connect(db_path)
        row3=db.execute("SELECT updated_at FROM public_clan_war_snapshot WHERE singleton=1").fetchone()
        db.close()
        deferred_unchanged=bool(row3 and int(row3[0])==original_updated and state=="unchanged")
        print("unread_war_leaves_cache_unchanged="+yes(deferred_unchanged))

        expired={**active,"ends_at":now-1}
        db=sqlite3.connect(db_path)
        db.execute("UPDATE public_clan_war_snapshot SET snapshot_json=?,source_player_id=?,updated_at=? WHERE singleton=1",
                   (json.dumps(expired,separators=(",",":")),mod.SOURCE,now-10))
        db.commit(); db.close()
        saved,state=mod.store_snapshot(True,None,{})
        db=sqlite3.connect(db_path)
        count=db.execute("SELECT COUNT(*) FROM public_clan_war_snapshot").fetchone()[0]
        db.close()
        expired_removed=(count==0 and state=="none")
        print("expired_war_removed="+yes(expired_removed))

        client_future={**active,"ends_at":now+3600}
        db=sqlite3.connect(db_path)
        db.execute("INSERT INTO public_clan_war_snapshot(singleton,snapshot_json,source_player_id,updated_at) VALUES(1,?,?,?)",
                   (json.dumps(client_future,separators=(",",":")),"anon-client",now))
        db.commit(); db.close()
        saved,state=mod.store_snapshot(True,None,{})
        db=sqlite3.connect(db_path)
        count=db.execute("SELECT COUNT(*) FROM public_clan_war_snapshot").fetchone()[0]
        db.close()
        client_not_authoritative=(count==0 and state=="none")
        print("client_snapshot_not_preserved="+yes(client_not_authoritative))

        power=[{"rank":1,"name":"Power One","value":100},{"rank":2,"name":"Power Two","value":90}]
        influence=[{"rank":1,"name":"Influence One","value":200}]
        saved,state=mod.store_snapshot(False,None,{"power":power,"influence":influence})
        db=sqlite3.connect(db_path)
        power_count=db.execute("SELECT COUNT(*) FROM public_rating_snapshots WHERE kind='power'").fetchone()[0]
        influence_before=db.execute("SELECT name,value,updated_at FROM public_rating_snapshots WHERE kind='influence' AND rank=1").fetchone()
        db.close()
        initial_ratings=(power_count==2 and influence_before is not None and set(saved)=={"power","influence"})
        print("ratings_initial_write="+yes(initial_ratings))

        time.sleep(1)
        new_power=[{"rank":1,"name":"Power New","value":120}]
        saved,state=mod.store_snapshot(False,None,{"power":new_power})
        db=sqlite3.connect(db_path)
        power_rows=db.execute("SELECT rank,name,value FROM public_rating_snapshots WHERE kind='power' ORDER BY rank").fetchall()
        influence_after=db.execute("SELECT name,value,updated_at FROM public_rating_snapshots WHERE kind='influence' AND rank=1").fetchone()
        db.close()
        partial_keeps_other=bool(
            power_rows==[(1,"Power New",120.0)]
            and influence_before==influence_after
            and saved==["power"]
        )
        print("ratings_partial_update_preserves_other_kinds="+yes(partial_keeps_other))

        invalid=[
            {"rank":1,"name":"Valid","value":10},
            {"rank":1,"name":"Duplicate","value":20},
            {"rank":101,"name":"Too Low Rank","value":30},
            {"rank":2,"name":"","value":40},
            {"rank":3,"name":"Negative","value":-1},
        ]
        saved,state=mod.store_snapshot(False,None,{"clans":invalid,"unknown_kind":[{"rank":1,"name":"X","value":1}]})
        db=sqlite3.connect(db_path)
        clan_rows=db.execute("SELECT rank,name,value FROM public_rating_snapshots WHERE kind='clans' ORDER BY rank").fetchall()
        unknown_count=db.execute("SELECT COUNT(*) FROM public_rating_snapshots WHERE kind='unknown_kind'").fetchone()[0]
        db.close()
        rating_sanitization=(clan_rows==[(1,"Valid",10.0)] and unknown_count==0 and saved==["clans"])
        print("ratings_sanitization="+yes(rating_sanitization))

        all_ok=all((
            active_written,
            state is not None,
            preserved,
            deferred_unchanged,
            expired_removed,
            client_not_authoritative,
            initial_ratings,
            partial_keeps_other,
            rating_sanitization,
        ))
        if not all_ok:
            raise SystemExit(2)
    finally:
        mod.DB_PATH=real_db

print("PUBLIC_COLLECTOR_CACHE_TRANSITIONS=PASS")
