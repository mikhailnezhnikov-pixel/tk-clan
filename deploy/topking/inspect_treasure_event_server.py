import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("SELECT assets_json FROM treasure_guide_captures WHERE assets_json<>''")]
urls=set()
for r in rows:
    try: arr=json.loads(r["assets_json"] or "[]")
    except: continue
    for a in arr:
        if re.search(r"/minigames/(?:fight|lights|fishing)/|lights_out|riddle|enemy",str(a),re.I):
            urls.add(str(a))
print("MECHANIC_ASSETS",json.dumps(sorted(urls),ensure_ascii=False))
