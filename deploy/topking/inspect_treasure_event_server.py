import importlib.util,json
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

wanted={"bp_event_minigame","bp_event_minigame_line_free","bp_event_minigame_line_paid_01","bp_event_minigame_line_paid_02"}
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE payload_json LIKE '%bp_event_minigame%'
                                          AND path LIKE '%#treasure-%'
                                        ORDER BY id DESC LIMIT 80""")]

found=[]
for r in rows:
    try: obj=json.loads(r["payload_json"])
    except: continue
    for x in obj.get("rows",[]) if isinstance(obj,dict) else []:
        if not isinstance(x,dict): continue
        p=x.get("payload")
        if not isinstance(p,dict): continue
        pid=str(p.get("id") or "")
        if pid in wanted:
            found.append({"capture":r["id"],"captured_at":r["captured_at"],"path":x.get("path"),"payload":p})
print("BP_PRIORITY",json.dumps(found,ensure_ascii=False))
