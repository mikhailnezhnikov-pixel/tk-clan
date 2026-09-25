import importlib.util, json, sqlite3, sys, math
SERVER=sys.argv[1] if len(sys.argv)>1 else '/opt/hamsterking-license/server.py'
DB=sys.argv[2] if len(sys.argv)>2 else '/var/lib/hamsterking-license/licenses.db'
spec=importlib.util.spec_from_file_location('hk_server',SERVER)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
db=sqlite3.connect(DB);db.row_factory=sqlite3.Row

def decode(flat):
    lng=lat=0;out=[]
    for off in range(0,len(flat)-2,3):
        lng+=int(flat[off]);lat+=int(flat[off+1]);flag=int(flat[off+2])
        out.append({'point_index':off//3,'lon':lng/100000.0,'lat':lat/100000.0,'room_count':flag&7})
    return out

def bbox(coords,out=None):
    if out is None: out=[math.inf,math.inf,-math.inf,-math.inf]
    if isinstance(coords,list):
        if len(coords)>=2 and isinstance(coords[0],(int,float)) and isinstance(coords[1],(int,float)):
            x=float(coords[0]);y=float(coords[1]);out[0]=min(out[0],x);out[1]=min(out[1],y);out[2]=max(out[2],x);out[3]=max(out[3],y)
        else:
            for child in coords:bbox(child,out)
    return out

rows=db.execute('''
 SELECT c.map_key,c.city,c.grid,c.buildings,c.unknown,c.c0,c.c1,c.c2,c.c3,c.c4,c.c5,
        al.canonical_area_id,p.points_json,g.geometry_json,g.feature_count
 FROM hk_maps_catalog c
 JOIN hk_map_area_links al ON al.map_key=c.map_key
 JOIN hk_map_points p ON p.map_key=c.map_key
 JOIN hk_map_area_geometry g ON g.canonical_area_id=al.canonical_area_id
 ORDER BY c.map_key
''').fetchall()
maps=[]
for row in rows:
    area=row['canonical_area_id']
    canonical={str(r['building_id']):dict(r) for r in db.execute(
      'SELECT building_id,room_count,knowledge_source FROM map_buildings WHERE area_id=?',(area,))}
    try: geom=json.loads(row['geometry_json'])
    except Exception: geom={}
    features={}
    for f in geom.get('features') or []:
        p=f.get('properties') or {}
        bid=str(p.get('building_id') or p.get('buildingId') or f.get('id') or p.get('id') or '').strip()
        if bid not in canonical or not isinstance(f.get('geometry'),dict):continue
        b=bbox(f['geometry'].get('coordinates'))
        if not all(math.isfinite(x) for x in b):continue
        features[bid]=(f['geometry'],b)
    try: flat=json.loads(row['points_json'] or '[]')
    except Exception: flat=[]
    points=decode(flat)
    matches={};ambiguous=0;unmatched=0
    for point in points:
        hits=[]
        x=point['lon'];y=point['lat']
        for bid,(geometry,b) in features.items():
            if bid in matches.values(): continue
            if x<b[0] or x>b[2] or y<b[1] or y>b[3]:continue
            if server._hk_upload_geometry_contains(geometry,x,y):hits.append(bid)
        if len(hits)==1:matches[point['point_index']]=hits[0]
        elif len(hits)>1:ambiguous+=1
        else:unmatched+=1
    conflicts=0;same=0
    source_hist={};current_for_source={}
    for point in points:
        r=point['room_count'];source_hist[str(r)]=source_hist.get(str(r),0)+1
        bid=matches.get(point['point_index'])
        if not bid:continue
        cur=canonical[bid]['room_count'];k='NULL' if cur is None else str(cur)
        current_for_source[k]=current_for_source.get(k,0)+1
        if cur is None or int(cur)!=r:conflicts+=1
        else:same+=1
    known_ids=set(matches.values())
    full_count_match=int(row['buildings'] or 0)==len(canonical)
    unknown_ids=set(canonical)-known_ids if full_count_match and len(matches)==len(points) else set()
    unknown_nonnull=sum(1 for bid in unknown_ids if canonical[bid]['room_count'] is not None)
    unknown_zero=sum(1 for bid in unknown_ids if canonical[bid]['room_count']==0)
    maps.append({
      'map_key':row['map_key'],'city':row['city'],'grid':row['grid'],
      'catalog_buildings':int(row['buildings'] or 0),'canonical_buildings':len(canonical),'geometry_game_ids':len(features),
      'source_points':len(points),'matched':len(matches),'unmatched':unmatched,'ambiguous':ambiguous,
      'source_conflicts':conflicts,'source_same':same,'source_hist':source_hist,'current_for_source':current_for_source,
      'full_count_match':full_count_match,'unknown_target':len(unknown_ids),'unknown_current_nonnull':unknown_nonnull,'unknown_current_zero':unknown_zero,
      'catalog_unknown':int(row['unknown'] or 0),
      'catalog_crystals':[int(row[f'c{i}'] or 0) for i in range(6)],
      'safe_full_repair':bool(full_count_match and len(features)==len(canonical) and len(matches)==len(points) and ambiguous==0 and len(unknown_ids)==int(row['unknown'] or 0)),
    })
out={
 'summary':{
   'geometry_maps':len(maps),
   'safe_full_repair_maps':sum(1 for m in maps if m['safe_full_repair']),
   'source_points':sum(m['source_points'] for m in maps),
   'matched':sum(m['matched'] for m in maps),
   'unmatched':sum(m['unmatched'] for m in maps),
   'ambiguous':sum(m['ambiguous'] for m in maps),
   'source_conflicts':sum(m['source_conflicts'] for m in maps),
   'unknown_to_restore':sum(m['unknown_target'] for m in maps if m['safe_full_repair']),
   'unknown_nonnull_to_clear':sum(m['unknown_current_nonnull'] for m in maps if m['safe_full_repair']),
   'unknown_zero_to_clear':sum(m['unknown_current_zero'] for m in maps if m['safe_full_repair']),
 },
 'lagos':[m for m in maps if m['city'].lower()=='lagos' and m['grid']=='33:22'],
 'maps':maps,
}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
db.close()
