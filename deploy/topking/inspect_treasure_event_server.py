import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures
                                        WHERE path LIKE '/client_config#treasure-%'
                                        ORDER BY id""")]

out=[]
for r in rows:
    try:obj=json.loads(r["payload_json"])
    except:continue
    for row in obj.get("rows",[]) if isinstance(obj,dict) else []:
        if not isinstance(row,dict):continue
        p=row.get("payload")
        if not isinstance(p,(dict,list)):continue
        blob=json.dumps(p,ensure_ascii=False,separators=(",",":"))
        low=blob.lower()
        if ("forest" not in low and "mine" not in low):continue
        if not (('"quantity":11' in blob and '"quantity":28' in blob) or ('"quantity":35' in blob and '"quantity":14' in blob)):
            continue
        out.append({"capture":r["id"],"row_path":row.get("path"),"payload":p})
print("ROOM_CONFIG",json.dumps(out,ensure_ascii=False))
