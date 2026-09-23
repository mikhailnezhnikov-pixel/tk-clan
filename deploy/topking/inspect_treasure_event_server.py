import importlib.util,json
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

terms=["bp_event_minigame_line_free","bp_event_minigame_line_paid_01","bp_event_minigame_line_paid_02"]
with server.db_session() as db:
    for term in terms:
        rows=db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures
                           WHERE payload_json LIKE ? ORDER BY id DESC LIMIT 30""",("%"+term+"%",)).fetchall()
        out=[]
        for r in rows:
            raw=str(r["payload_json"] or "")
            pos=raw.find(term)
            out.append({"id":r["id"],"path":r["path"],"snippet":raw[max(0,pos-900):pos+2200]})
        print("LINE",term,json.dumps(out,ensure_ascii=False))
