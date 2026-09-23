import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures
                                        WHERE path LIKE '/client_config#treasure-%'
                                        ORDER BY id""")]

need=("bp_event_minigame","bp_event_minigame_line_free","bp_event_minigame_line_paid_01","bp_event_minigame_line_paid_02")
out=[]
for r in rows:
    try:obj=json.loads(r["payload_json"])
    except:continue
    for row in obj.get("rows",[]) if isinstance(obj,dict) else []:
        if not isinstance(row,dict):continue
        p=row.get("payload")
        if not isinstance(p,(dict,list)):continue
        blob=json.dumps(p,ensure_ascii=False,separators=(",",":"))
        if any(x in blob for x in need):
            out.append({"capture":r["id"],"capture_path":r["path"],"row_path":row.get("path"),"payload":p})
print("BP_CONFIG_ROWS",json.dumps(out,ensure_ascii=False))
