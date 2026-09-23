import importlib.util,json
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

need={"bp_event_minigame","bp_event_minigame_line_free","bp_event_minigame_line_paid_01","bp_event_minigame_line_paid_02"}
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,captured_at FROM treasure_guide_captures
                                        WHERE path LIKE '/client_config#treasure-%' OR path LIKE '/battlepass#treasure-%'
                                        ORDER BY id DESC LIMIT 120""")]

out=[]
for r in rows:
    try:obj=json.loads(r["payload_json"])
    except:continue
    for row in obj.get("rows",[]) if isinstance(obj,dict) else []:
        p=row.get("payload") if isinstance(row,dict) else None
        if isinstance(p,dict) and str(p.get("id") or "") in need:
            out.append({"capture":r["id"],"captured_at":r["captured_at"],"path":r["path"],"payload":p})
print("BP_PRIORITY",json.dumps(out,ensure_ascii=False))
