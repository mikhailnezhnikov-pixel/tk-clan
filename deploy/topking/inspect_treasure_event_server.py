import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,source,path,payload_json,page_text,assets_json,captured_at
                                        FROM treasure_guide_captures
                                        ORDER BY id""")]
    print("TREASURE_COUNT",len(rows))
    selective=[r for r in rows if "#treasure-" in str(r["path"])]
    print("SELECTIVE_COUNT",len(selective))
    print("SELECTIVE_META",json.dumps([
      {"id":r["id"],"path":r["path"],"len":len(r["payload_json"] or ""), "captured_at":r["captured_at"]}
      for r in selective[-80:]
    ],ensure_ascii=False))
    for r in selective[-20:]:
        payload=str(r["payload_json"] or "")
        print("SELECTIVE_SAMPLE",r["id"],r["path"],payload[:30000])

    # Inspect all DB tables for cached/static game documents.
    tables=[x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    print("TABLES",json.dumps(tables,ensure_ascii=False))
    for t in tables:
        low=t.lower()
        if not any(k in low for k in ("static","document","cache","shop","fair","item","event","config")):
            continue
        try:
            cols=[dict(x) for x in db.execute(f"PRAGMA table_info({t})")]
            print("TABLE_SCHEMA",t,json.dumps(cols,ensure_ascii=False))
            cnt=db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print("TABLE_COUNT",t,cnt)
            if cnt and cnt<50000:
                sample=[dict(x) for x in db.execute(f"SELECT * FROM {t} ORDER BY rowid DESC LIMIT 20")]
                txt=json.dumps(sample,ensure_ascii=False)
                print("TABLE_SAMPLE",t,txt[:30000])
        except Exception as e:
            print("TABLE_ERROR",t,repr(e))
