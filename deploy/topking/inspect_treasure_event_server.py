import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("SELECT id,path,page_text,captured_at FROM treasure_guide_captures ORDER BY id")]

for kw in ["Торговец","Сундук","Сундуки","Рыбалка","Сокровищница","Питомцы","Поручения питомцам","Сражение"]:
    vals=[];seen=set()
    for r in rows:
        t=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
        if kw.lower() not in t.lower() or len(t)>2200: continue
        pos=t.rfind(" HK ")
        body=t[pos+4:] if pos>=0 else t
        if body in seen: continue
        seen.add(body)
        vals.append({"id":r["id"],"len":len(body),"body":body[:1800]})
    print("SCREEN",kw,json.dumps(vals[-30:],ensure_ascii=False))
