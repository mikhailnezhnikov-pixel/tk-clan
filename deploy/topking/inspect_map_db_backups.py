import glob, json, os, sqlite3, sys, time
root='/var/lib/hamsterking-license'
live=os.path.join(root,'licenses.db')
patterns=[live+'.bak*',os.path.join(root,'*licenses*.db*'),os.path.join(root,'*.bak*')]
files=sorted(set(p for pat in patterns for p in glob.glob(pat) if os.path.isfile(p)))
if live not in files: files.insert(0,live)

def inspect(path):
    out={'path':path,'size':os.path.getsize(path),'mtime':int(os.path.getmtime(path))}
    try:
        db=sqlite3.connect('file:'+path+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        out['tables']=len(tables)
        if 'hk_full_import_batches' in tables:
            out['full_batches']=[dict(r) for r in db.execute("SELECT batch_id,archive_sha256,exported_at,created_at,status FROM hk_full_import_batches ORDER BY created_at")]
        if 'hk_full_map_import_links' in tables:
            out['full_links']=db.execute("SELECT COUNT(*) FROM hk_full_map_import_links").fetchone()[0]
            row=db.execute("SELECT MIN(imported_at),MAX(imported_at),COUNT(DISTINCT archive_sha256) FROM hk_full_map_import_links").fetchone()
            out['full_link_times']=list(row)
        if {'hk_maps_catalog','hk_map_area_links','map_buildings'} <= tables:
            lag=db.execute("""SELECT al.canonical_area_id FROM hk_maps_catalog c
                              JOIN hk_map_area_links al ON al.map_key=c.map_key
                              WHERE lower(c.city)='lagos' AND c.grid='33:22'""").fetchone()
            if lag:
                aid=lag[0]
                out['lagos_area']=aid
                out['lagos_hist']=[dict(r) for r in db.execute("""SELECT CASE WHEN room_count IS NULL THEN 'NULL' ELSE CAST(room_count AS TEXT) END room,
                                    knowledge_source,COUNT(*) n FROM map_buildings WHERE area_id=? GROUP BY room,knowledge_source ORDER BY room,knowledge_source""",(aid,))]
                out['lagos_total']=db.execute("SELECT COUNT(*) FROM map_buildings WHERE area_id=?",(aid,)).fetchone()[0]
        db.close()
    except Exception as e:
        out['error']=repr(e)
    return out
print(json.dumps([inspect(p) for p in files],ensure_ascii=False,sort_keys=True))
