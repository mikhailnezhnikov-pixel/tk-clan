import importlib.util, json, time, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
      SELECT id,path,payload_json,captured_at
      FROM treasure_guide_captures
      WHERE captured_at>=?
        AND payload_json LIKE '%fair_mini_game_fight%'
      ORDER BY id DESC
      LIMIT 160
    """,(int(time.time())-6*3600,))]

seen=set()
for r in rows:
    raw=str(r.get("payload_json") or "")
    try: obj=json.loads(raw)
    except: continue
    payloads=[]
    if isinstance(obj,dict) and isinstance(obj.get("rows"),list):
        payloads=[x.get("payload") for x in obj["rows"] if isinstance(x,dict)]
    else:
        payloads=[obj]
    for p in payloads:
        if not isinstance(p,dict): continue
        # Direct fair object.
        if p.get("id")=="fair_mini_game_fight" and isinstance(p.get("fair_slots"),list):
            key=(r["id"],json.dumps(p["fair_slots"],sort_keys=True,ensure_ascii=False))
            if key in seen: continue
            seen.add(key)
            print("FIGHT",r["id"],r["captured_at"],r["path"],json.dumps(p["fair_slots"],ensure_ascii=False,separators=(",",":")))
        # Whole API state.
        fairs=p.get("fair")
        if isinstance(fairs,list):
            for f in fairs:
                if isinstance(f,dict) and f.get("id")=="fair_mini_game_fight":
                    key=(r["id"],json.dumps(f.get("fair_slots"),sort_keys=True,ensure_ascii=False))
                    if key in seen: continue
                    seen.add(key)
                    print("FIGHT",r["id"],r["captured_at"],r["path"],json.dumps(f.get("fair_slots") or [],ensure_ascii=False,separators=(",",":")))
