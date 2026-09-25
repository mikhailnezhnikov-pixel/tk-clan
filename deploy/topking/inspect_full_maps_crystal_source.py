import importlib.util, json, sqlite3, sys
SERVER=sys.argv[1] if len(sys.argv)>1 else '/opt/hamsterking-license/server.py'
DB=sys.argv[2] if len(sys.argv)>2 else '/var/lib/hamsterking-license/licenses.db'
spec=importlib.util.spec_from_file_location('hk_server',SERVER)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
db=sqlite3.connect(DB); db.row_factory=sqlite3.Row
rows=db.execute('''
 SELECT c.map_key,c.city,c.grid,c.buildings,c.unknown,al.canonical_area_id
 FROM hk_maps_catalog c
 LEFT JOIN hk_map_area_links al ON al.map_key=c.map_key
 ORDER BY c.map_key
''').fetchall()
summary={'maps':0,'full_maps':0,'full_game_buildings':0,'with_building_ids':0,'source_known':0,'source_unknown':0,'id_overlap':0,'id_missing_in_canonical':0}
details=[]
for row in rows:
    summary['maps']+=1
    key=row['map_key']; area=row['canonical_area_id']
    full=server.load_full_hk_map(key)
    if not full:
        details.append({'map_key':key,'city':row['city'],'grid':row['grid'],'full':False})
        continue
    summary['full_maps']+=1
    feats=(full.get('buildings') or {}).get('features') or []
    game=[]
    for f in feats:
        p=f.get('properties') or {}
        if not p.get('is_game'): continue
        bid=str(p.get('building_id') or f.get('id') or '').strip()
        val=p.get('crystals',None)
        if val is None and 'crystals_key' in p and str(p.get('crystals_key'))!='NULL':
            try: val=int(p.get('crystals_key'))
            except Exception: val=None
        try: val=None if val is None else int(val)
        except Exception: val=None
        game.append((bid,val))
    source_ids={bid for bid,_ in game if bid}
    known=sum(1 for _,v in game if v is not None)
    unknown=sum(1 for _,v in game if v is None)
    canonical_ids=set()
    if area:
        canonical_ids={str(r['building_id']) for r in db.execute('SELECT building_id FROM map_buildings WHERE area_id=?',(area,))}
    overlap=len(source_ids & canonical_ids)
    missing=len(source_ids-canonical_ids)
    summary['full_game_buildings']+=len(game)
    summary['with_building_ids']+=len(source_ids)
    summary['source_known']+=known
    summary['source_unknown']+=unknown
    summary['id_overlap']+=overlap
    summary['id_missing_in_canonical']+=missing
    hist={}
    for _,v in game:
        k='NULL' if v is None else str(v)
        hist[k]=hist.get(k,0)+1
    details.append({
      'map_key':key,'city':row['city'],'grid':row['grid'],'full':True,
      'catalog_buildings':int(row['buildings'] or 0),'full_game_buildings':len(game),
      'source_ids':len(source_ids),'canonical_ids':len(canonical_ids),'id_overlap':overlap,'id_missing':missing,
      'source_hist':hist,
    })
out={'summary':summary,'lagos':[d for d in details if d.get('city','').lower()=='lagos' and d.get('grid')=='33:22'],'maps':details}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
db.close()
