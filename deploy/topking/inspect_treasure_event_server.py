import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("SELECT id,path,payload_json FROM treasure_guide_captures WHERE payload_json<>'' ORDER BY id")]

loc=[{"id":r["id"],"path":r["path"],"len":len(r["payload_json"] or "")} for r in rows if "local" in str(r["path"]).lower()]
print("LOCALIZATION_ROWS",json.dumps(loc,ensure_ascii=False))

terms=[f"item_{kind}_t{n}" for n in range(1,6) for kind in ("box","food","water")]
for term in terms:
    hits=[]
    for r in rows:
        raw=str(r["payload_json"] or "")
        for key in (term+"_name",term):
            pos=raw.find(key)
            if pos>=0:
                hits.append({"id":r["id"],"path":r["path"],"snippet":raw[max(0,pos-250):pos+800]})
                break
        if len(hits)>=10:break
    print("LOC_TERM",term,json.dumps(hits,ensure_ascii=False))
