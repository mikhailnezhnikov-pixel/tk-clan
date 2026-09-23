import importlib.util, json

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures
                                        WHERE path LIKE '/shop/view#treasure-%'
                                        ORDER BY id""")]
for r in rows:
    obj=json.loads(r["payload_json"])
    arr=obj.get("rows",[])
    print("CAPTURE",r["id"],r["path"],"ROWS",len(arr))
    for idx,item in enumerate(arr[:40]):
        payload=item.get("payload")
        print("ROW",idx,"PATH",item.get("path"),"PAYLOAD_TYPE",type(payload).__name__,"ID",payload.get("id") if isinstance(payload,dict) else None,"KEYS",list(payload.keys())[:12] if isinstance(payload,dict) else None)
