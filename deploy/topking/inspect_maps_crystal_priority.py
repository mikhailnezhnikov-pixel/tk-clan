import json, sqlite3, sys
DB=sys.argv[1] if len(sys.argv)>1 else '/var/lib/hamsterking-license/licenses.db'
db=sqlite3.connect(DB); db.row_factory=sqlite3.Row

def q(sql,args=()):
    return [dict(r) for r in db.execute(sql,args)]

def scalar(sql,args=()):
    row=db.execute(sql,args).fetchone()
    return None if row is None else row[0]

out={
  'catalog_total': scalar('SELECT COUNT(*) FROM hk_maps_catalog'),
  'area_links': scalar('SELECT COUNT(*) FROM hk_map_area_links'),
  'point_links': scalar('SELECT COUNT(*) FROM hk_map_point_links'),
  'map_buildings': scalar('SELECT COUNT(*) FROM map_buildings'),
  'provenance': q('SELECT knowledge_source,COUNT(*) n FROM map_buildings GROUP BY knowledge_source ORDER BY knowledge_source'),
  'area_link_methods': q('SELECT match_method,COUNT(*) n FROM hk_map_area_links GROUP BY match_method ORDER BY match_method'),
  'linked_room_sources': q('''
    SELECT mb.knowledge_source,mb.room_count,COUNT(*) n
    FROM hk_map_point_links pl
    JOIN hk_map_area_links al ON al.map_key=pl.map_key
    JOIN map_buildings mb ON mb.area_id=al.canonical_area_id AND mb.building_id=pl.building_id
    GROUP BY mb.knowledge_source,mb.room_count
    ORDER BY mb.knowledge_source,mb.room_count
  '''),
  'lagos_catalog': q("SELECT map_key,city,grid,buildings,unknown,c0,c1,c2,c3,c4,c5 FROM hk_maps_catalog WHERE lower(city)='lagos' AND grid='33:22'"),
}

comparisons=[]
for row in db.execute('''
  SELECT c.map_key,c.city,c.grid,c.buildings,c.unknown,c.c0,c.c1,c.c2,c.c3,c.c4,c.c5,
         al.canonical_area_id,p.points_json,p.point_count
  FROM hk_maps_catalog c
  JOIN hk_map_area_links al ON al.map_key=c.map_key
  JOIN hk_map_points p ON p.map_key=c.map_key
  ORDER BY c.map_key
'''):
    map_key=row['map_key']; area_id=row['canonical_area_id']
    try: flat=json.loads(row['points_json'] or '[]')
    except Exception: flat=[]
    source={}
    for i in range(0,len(flat)-2,3):
        source[i//3]=int(flat[i+2]) & 0x07
    links={int(r['point_index']):r['building_id'] for r in db.execute(
        'SELECT point_index,building_id FROM hk_map_point_links WHERE map_key=?',(map_key,))}
    canonical={r['building_id']:(r['room_count'],r['knowledge_source']) for r in db.execute(
        'SELECT building_id,room_count,knowledge_source FROM map_buildings WHERE area_id=?',(area_id,))}
    matched=conflicts=missing_links=0
    conflict_hist={}
    source_hist={}
    canonical_link_hist={}
    for idx,rooms in source.items():
        source_hist[str(rooms)]=source_hist.get(str(rooms),0)+1
        bid=links.get(idx)
        if not bid:
            missing_links+=1; continue
        if bid not in canonical:
            continue
        matched+=1
        can,ks=canonical[bid]
        key='NULL' if can is None else str(can)
        canonical_link_hist[key]=canonical_link_hist.get(key,0)+1
        if can is None or int(can)!=rooms:
            conflicts+=1
            ck=f'{rooms}->{key}'
            conflict_hist[ck]=conflict_hist.get(ck,0)+1
    canonical_count=len(canonical)
    comparisons.append({
      'map_key':map_key,'city':row['city'],'grid':row['grid'],
      'catalog_buildings':int(row['buildings'] or 0),'canonical_buildings':canonical_count,
      'counts_match':int(row['buildings'] or 0)==canonical_count,
      'source_points':len(source),'linked_points':len(links),'matched_points':matched,
      'unlinked_source_points':missing_links,'source_conflicts':conflicts,
      'source_hist':source_hist,'canonical_link_hist':canonical_link_hist,'conflict_hist':conflict_hist,
      'catalog_unknown':int(row['unknown'] or 0),
      'catalog_crystals':[int(row[f'c{i}'] or 0) for i in range(6)],
    })

out['linked_maps']=comparisons
out['linked_summary']={
  'maps':len(comparisons),
  'count_matched_maps':sum(1 for r in comparisons if r['counts_match']),
  'source_points':sum(r['source_points'] for r in comparisons),
  'linked_points':sum(r['linked_points'] for r in comparisons),
  'source_conflicts':sum(r['source_conflicts'] for r in comparisons),
  'unlinked_source_points':sum(r['unlinked_source_points'] for r in comparisons),
}
out['lagos_linked']=[r for r in comparisons if r['city'].lower()=='lagos' and r['grid']=='33:22']
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
db.close()
