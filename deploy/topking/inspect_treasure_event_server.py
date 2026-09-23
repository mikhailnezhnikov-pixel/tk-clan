import importlib.util, json, collections

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,page_text FROM treasure_guide_captures ORDER BY id""")]

cnt=collections.Counter(r["path"] for r in rows)
print("PATH_COUNTS",json.dumps(cnt.most_common(),ensure_ascii=False))
for r in rows:
    p=str(r["path"] or "")
    if "local" in p.lower() or "text" in p.lower() or "lang" in p.lower():
        print("TEXT_CAPTURE",r["id"],p,len(r["payload_json"] or ""),str(r["payload_json"] or "")[:12000])
