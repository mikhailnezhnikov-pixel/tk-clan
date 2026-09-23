import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures
                                        WHERE path LIKE '%#treasure-%' ORDER BY id""")]

rx=re.compile(r"pet_skill|treasurelot_chest|trader_02|trader_03|fishing_rod|sword|treasury_room",re.I)
hits=[]
for r in rows:
    try: obj=json.loads(r["payload_json"] or "{}")
    except: continue
    arr=obj.get("rows",[]) if isinstance(obj,dict) else []
    for item in arr if isinstance(arr,list) else []:
        payload=item.get("payload") if isinstance(item,dict) else None
        if not isinstance(payload,dict): continue
        oid=str(payload.get("id") or "")
        if oid and rx.search(oid):
            hits.append({"capture":r["id"],"source":r["path"],"json_path":item.get("path"),"id":oid,"object":payload})
print("DIRECT_MATCHES",json.dumps(hits,ensure_ascii=False))
