import importlib.util,json
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

terms=["bp_event_minigame_line_free","bp_event_minigame_line_paid_01","bp_event_minigame_line_paid_02"]
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE path LIKE '/client_config%'
                                          AND payload_json<>''
                                        ORDER BY id DESC""")]

for term in terms:
    hits=[]
    for r in rows:
        raw=str(r["payload_json"] or "")
        start=0
        while True:
            pos=raw.find(term,start)
            if pos<0: break
            hits.append({
              "id":r["id"],"path":r["path"],"captured_at":r["captured_at"],
              "snippet":raw[max(0,pos-2500):pos+9000]
            })
            start=pos+len(term)
            if len(hits)>=12: break
        if len(hits)>=12: break
    print("CFG_LINE",term,json.dumps(hits,ensure_ascii=False))
