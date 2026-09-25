import json, sqlite3, sys, time, os
LIVE=sys.argv[1] if len(sys.argv)>1 else '/var/lib/hamsterking-license/licenses.db'
SOURCE=sys.argv[2] if len(sys.argv)>2 else '/var/lib/hamsterking-license/licenses.db.bak.full235.20260921-053021'
EXPECTED_SHA='a4b84c5239168182702090efe0b7241b54295942d63e5f020539092694e0a3e1'

src=sqlite3.connect('file:'+SOURCE+'?mode=ro',uri=True);src.row_factory=sqlite3.Row
live=sqlite3.connect(LIVE);live.row_factory=sqlite3.Row
batch=src.execute("SELECT batch_id,archive_sha256,exported_at FROM hk_full_import_batches ORDER BY created_at DESC LIMIT 1").fetchone()
if not batch or batch['archive_sha256']!=EXPECTED_SHA:
    raise SystemExit('unexpected Full235 source archive')
stage=src.execute("SELECT map_key,city,grid,buildings_json,building_count FROM hk_full_import_stage WHERE batch_id=? ORDER BY map_key",(batch['batch_id'],)).fetchall()
if len(stage)!=235:
    raise SystemExit(f'expected 235 source maps, got {len(stage)}')
try:
    observed_at=int(__import__('datetime').datetime.fromisoformat(str(batch['exported_at']).replace('Z','+00:00')).timestamp())
except Exception:
    observed_at=int(time.time())
now=int(time.time())

live.execute("""CREATE TABLE IF NOT EXISTS hk_map_source_crystals(
    map_key TEXT NOT NULL,
    canonical_area_id TEXT NOT NULL,
    building_id TEXT NOT NULL,
    room_count INTEGER,
    is_invest INTEGER NOT NULL DEFAULT 0,
    observed_at INTEGER NOT NULL DEFAULT 0,
    source TEXT NOT NULL DEFAULT 'full235_archive',
    PRIMARY KEY(map_key,building_id)
)""")
live.execute("""CREATE INDEX IF NOT EXISTS idx_hk_map_source_crystals_area_building
                ON hk_map_source_crystals(canonical_area_id,building_id)""")

maps=source_rows=updated=inserted=extras=0
lagos=None
with live:
    live.execute("DELETE FROM hk_map_source_crystals")
    for row in stage:
        key=str(row['map_key'])
        buildings=json.loads(row['buildings_json'])
        link=live.execute("SELECT canonical_area_id FROM hk_map_area_links WHERE map_key=?",(key,)).fetchone()
        if not link:
            raise RuntimeError(f'missing canonical link for {key}')
        aid=str(link['canonical_area_id'])
        current={str(r['building_id']):dict(r) for r in live.execute(
            "SELECT building_id,room_count,knowledge_source FROM map_buildings WHERE area_id=?",(aid,))}
        source_ids={str(item[0]) for item in buildings}
        missing=source_ids-set(current)
        if missing:
            raise RuntimeError(f'{key}: source building ids missing from canonical: {len(missing)}')
        extras+=len(set(current)-source_ids)
        hist={None:0,0:0,1:0,2:0,3:0,4:0,5:0}
        invest_count=0
        for item in buildings:
            bid=str(item[0]);room=item[1];is_invest=int(bool(item[2]))
            invest_count+=is_invest
            if room in hist: hist[room]+=1
            live.execute("""INSERT INTO hk_map_source_crystals(
                map_key,canonical_area_id,building_id,room_count,is_invest,observed_at,source)
                VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(map_key,building_id) DO UPDATE SET
                canonical_area_id=excluded.canonical_area_id,
                room_count=excluded.room_count,
                is_invest=excluded.is_invest,
                observed_at=excluded.observed_at,
                source=excluded.source""",
                (key,aid,bid,room,is_invest,observed_at,'full235_archive'))
            before=current[bid]
            if before['room_count']!=room or before['knowledge_source']!='hk_maps_import':
                updated+=1
            live.execute("""UPDATE map_buildings SET
                room_count=?,
                has_events=?,
                is_invest=MAX(is_invest,?),
                last_player_id='source-hk-maps-import',
                last_seen=MAX(last_seen,?),
                knowledge_source='hk_maps_import',
                knowledge_observed_at=?
                WHERE area_id=? AND building_id=?""",
                (room,int(room is not None and int(room)>0),is_invest,now,observed_at,aid,bid))
            source_rows+=1
        # The full uploaded archive is the authoritative per-building source.
        # Keep the website catalog counters aligned with that same source.
        live.execute("""UPDATE hk_maps_catalog SET
            buildings=?,invest=?,unknown=?,c0=?,c1=?,c2=?,c3=?,c4=?,c5=?,updated_at=?
            WHERE map_key=?""",
            (len(buildings),invest_count,hist[None],hist[0],hist[1],hist[2],hist[3],hist[4],hist[5],now,key))
        maps+=1
        if key=='hk_lagos3322':
            lagos={'map_key':key,'buildings':len(buildings),'unknown':hist[None],
                   'c0':hist[0],'c1':hist[1],'c2':hist[2],'c3':hist[3],'c4':hist[4],'c5':hist[5]}

# Strong post-migration verification.
source_table=live.execute("SELECT COUNT(*) FROM hk_map_source_crystals").fetchone()[0]
if source_table!=source_rows:
    raise RuntimeError(f'source table mismatch {source_table}!={source_rows}')
bad=0
for row in stage:
    key=str(row['map_key']);buildings=json.loads(row['buildings_json'])
    aid=live.execute("SELECT canonical_area_id FROM hk_map_area_links WHERE map_key=?",(key,)).fetchone()[0]
    for item in buildings:
        bid=str(item[0]);room=item[1]
        cur=live.execute("""SELECT room_count,knowledge_source FROM map_buildings
                            WHERE area_id=? AND building_id=?""",(aid,bid)).fetchone()
        if not cur or cur['room_count']!=room or cur['knowledge_source']!='hk_maps_import':
            bad+=1
            if bad>20:break
    if bad>20:break
if bad:
    raise RuntimeError(f'post-migration source priority mismatches: {bad}')

if lagos != {'map_key':'hk_lagos3322','buildings':1078,'unknown':955,'c0':1,'c1':6,'c2':101,'c3':15,'c4':0,'c5':0}:
    raise RuntimeError(f'Lagos 33:22 source mismatch: {lagos}')

out={'ok':True,'maps':maps,'source_rows':source_rows,'rows_restored':updated,'extra_live_ids':extras,
     'source_table_rows':source_table,'archive_sha256':EXPECTED_SHA,'exported_at':batch['exported_at'],'lagos_33_22':lagos}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
src.close();live.close()
