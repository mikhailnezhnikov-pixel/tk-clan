import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json
                                        FROM treasure_guide_captures
                                        WHERE payload_json<>'' ORDER BY id""")]

terms=re.compile(r"mf_pm_.*_r4",re.I)
hits=[]
for r in rows:
    raw=str(r.get("payload_json") or "")
    if not terms.search(raw):
        continue
    for m in terms.finditer(raw):
        start=max(0,m.start()-1800); end=min(len(raw),m.end()+5000)
        hits.append({"id":r["id"],"path":r["path"],"snippet":raw[start:end]})
        if len(hits)>=40: break
    if len(hits)>=40: break
print("R4_LOTS",json.dumps(hits,ensure_ascii=False))
