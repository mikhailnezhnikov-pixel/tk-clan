import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

terms=[
 "treasure_minigame_rod_r1","treasure_minigame_rod_r2","treasure_minigame_rod_r3","treasure_minigame_rod_r4",
 "treasure_minigame_sword_r1","treasure_minigame_sword_r2","treasure_minigame_sword_r3","treasure_minigame_sword_r4",
 "chainmail","armor"
]
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,page_text FROM treasure_guide_captures
                                        WHERE payload_json<>'' OR page_text<>''
                                        ORDER BY id""")]

for term in terms:
    hits=[]
    for r in rows:
        for field in ("payload_json","page_text"):
            raw=str(r.get(field) or "")
            pos=raw.lower().find(term.lower())
            if pos<0: continue
            hits.append({
              "id":r["id"],"path":r["path"],"field":field,
              "snippet":raw[max(0,pos-1000):pos+3200]
            })
            if len(hits)>=12: break
        if len(hits)>=12: break
    print("EQ",term,json.dumps(hits,ensure_ascii=False))
