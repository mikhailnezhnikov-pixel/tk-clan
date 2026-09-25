import json, sqlite3, sys, os
LIVE=sys.argv[1] if len(sys.argv)>1 else '/var/lib/hamsterking-license/licenses.db'
SOURCE=sys.argv[2] if len(sys.argv)>2 else '/var/lib/hamsterking-license/licenses.db.bak.full235.20260921-053021'
src=sqlite3.connect('file:'+SOURCE+'?mode=ro',uri=True);src.row_factory=sqlite3.Row
live=sqlite3.connect('file:'+LIVE+'?mode=ro',uri=True);live.row_factory=sqlite3.Row
batches=src.execute("SELECT batch_id,archive_sha256,exported_at,status FROM hk_full_import_batches ORDER BY created_at DESC").fetchall()
if len(batches)!=1: raise SystemExit(f'unexpected source batches: {len(batches)}')
batch=batches[0]
stage=src.execute("SELECT map_key,city,grid,buildings_json,building_count FROM hk_full_import_stage WHERE batch_id=? ORDER BY map_key",(batch['batch_id'],)).fetchall()
if len(stage)!=235: raise SystemExit(f'expected 235 staged maps, got {len(stage)}')
maps=[];total_source=overlap=missing=extra=changes=0;hist_mismatch=0
for row in stage:
    key=str(row['map_key']);buildings=json.loads(row['buildings_json'])
    link=live.execute("SELECT canonical_area_id FROM hk_map_area_links WHERE map_key=?",(key,)).fetchone()
    if not link:
        maps.append({'map_key':key,'error':'missing_link'});continue
    aid=str(link[0])
    current={str(r['building_id']):dict(r) for r in live.execute("SELECT building_id,room_count,knowledge_source FROM map_buildings WHERE area_id=?",(aid,))}
    source={str(x[0]):x for x in buildings}
    sids=set(source);cids=set(current)
    ov=sids&cids;mis=sids-cids;ext=cids-sids
    changed=sum(1 for bid in ov if current[bid]['room_count'] != source[bid][1] or current[bid]['knowledge_source']!='hk_maps_import')
    hist={}
    for x in buildings:
        k='NULL' if x[1] is None else str(int(x[1]));hist[k]=hist.get(k,0)+1
    cat=live.execute("SELECT buildings,unknown,c0,c1,c2,c3,c4,c5 FROM hk_maps_catalog WHERE map_key=?",(key,)).fetchone()
    cat_hist={'NULL':int(cat['unknown'] or 0), **{str(i):int(cat[f'c{i}'] or 0) for i in range(6)}} if cat else {}
    same_hist=all(hist.get(k,0)==v for k,v in cat_hist.items()) and sum(hist.values())==int(cat['buildings'] or 0)
    if not same_hist:hist_mismatch+=1
    maps.append({'map_key':key,'city':row['city'],'grid':row['grid'],'area_id':aid,
                 'source_buildings':len(source),'current_buildings':len(current),'overlap':len(ov),'missing_source_ids':len(mis),'extra_live_ids':len(ext),
                 'rows_to_restore':changed+len(mis),'source_hist':hist,'catalog_hist':cat_hist,'catalog_hist_match':same_hist,
                 'missing_sample':sorted(mis)[:10],'extra_sample':sorted(ext)[:10]})
    total_source+=len(source);overlap+=len(ov);missing+=len(mis);extra+=len(ext);changes+=changed+len(mis)
out={'source':{'path':SOURCE,'batch_id':batch['batch_id'],'archive_sha256':batch['archive_sha256'],'exported_at':batch['exported_at'],'maps':len(stage)},
     'summary':{'source_buildings':total_source,'id_overlap':overlap,'missing_source_ids':missing,'extra_live_ids':extra,'rows_to_restore':changes,'catalog_hist_mismatch_maps':hist_mismatch,
                'exact_id_maps':sum(1 for m in maps if m.get('missing_source_ids')==0 and m.get('extra_live_ids')==0)},
     'lagos':[m for m in maps if m.get('city','').lower()=='lagos' and m.get('grid')=='33:22'],
     'non_exact_maps':[m for m in maps if m.get('missing_source_ids') or m.get('extra_live_ids')],
     'hist_mismatch_maps':[m for m in maps if m.get('catalog_hist_match') is False]}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
src.close();live.close()
