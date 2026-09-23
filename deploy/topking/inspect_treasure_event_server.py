import importlib.util, json
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    row=db.execute("SELECT id,path,payload_json FROM treasure_guide_captures WHERE path LIKE '/fair/reroll#treasure-%' ORDER BY id DESC LIMIT 1").fetchone()
obj=json.loads(row["payload_json"])
rows=obj.get("rows",[])
out=[]
for x in rows:
    if not isinstance(x,dict): continue
    p=str(x.get("path") or "")
    payload=x.get("payload")
    keys=list(payload.keys())[:30] if isinstance(payload,dict) else []
    pid=payload.get("id") if isinstance(payload,dict) else None
    out.append({"path":p,"id":pid,"keys":keys})
print("META",row["id"],row["path"],len(rows))
print("ROWS",json.dumps(out,ensure_ascii=False))
