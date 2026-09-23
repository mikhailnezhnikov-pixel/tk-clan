import importlib.util, json, collections

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("SELECT id,path,payload_json,page_text,captured_at FROM treasure_guide_captures ORDER BY id")]
counts=collections.Counter(r["path"] for r in rows)
print("PATH_COUNTS",json.dumps(counts,ensure_ascii=False))
for r in rows:
    if str(r["path"]).startswith("/localization/"):
        p=str(r["payload_json"] or "")
        print("LOCALIZATION",r["id"],r["path"],len(p),p[:1000],p[-500:])
