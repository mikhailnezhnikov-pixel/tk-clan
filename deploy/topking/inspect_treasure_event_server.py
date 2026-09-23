import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("SELECT id,path,page_text FROM treasure_guide_captures WHERE page_text<>'' ORDER BY id")]
out=[]
for r in rows:
    text=re.sub(r"\\s+"," ",str(r.get("page_text") or "")).strip()
    if len(text)>3000:
        continue
    if any(x.lower() in text.lower() for x in ["питом","корм","навык","s+","ключ","рыбал","hp"]):
        out.append({"id":r["id"],"path":r["path"],"text":text})
print("DOM_PET",json.dumps(out[-120:],ensure_ascii=False))
