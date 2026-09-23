import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,page_text FROM treasure_guide_captures
                                        WHERE page_text<>'' ORDER BY id""")]

for rank in ["B","A","S","S+"]:
    out=[]
    rx=re.compile(rf"·\s*{re.escape(rank)}(?:\s|$)",re.I)
    for r in rows:
        text=re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()
        if not rx.search(text) or "СОДЕРЖИТ" not in text: continue
        pos=text.find("СОДЕРЖИТ")
        # find last pet name marker before contains by cutting modal tail
        tail=text[max(0,pos-180):pos+800]
        out.append({"id":r["id"],"snippet":tail})
    print("PET_RANK",rank,json.dumps(out[:30],ensure_ascii=False))
