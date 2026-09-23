import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

terms=[
 "chest_type_015","chest_type_01","chest_type_02","chest_type_03",
 "digging_spot","treasury_room_choose_way_2","treasury_ways",
 "minigame_chests","treasure_chests"
]

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json
                                        FROM treasure_guide_captures
                                        WHERE path LIKE '/client_config#treasure-%'
                                        ORDER BY id""")]

for term in terms:
    out=[]
    for r in rows:
        try:obj=json.loads(r["payload_json"])
        except:continue
        for x in obj.get("rows",[]) if isinstance(obj,dict) else []:
            if not isinstance(x,dict):continue
            blob=json.dumps(x,ensure_ascii=False,separators=(",",":"))
            if term.lower() in blob.lower():
                out.append({
                  "capture":r["id"],
                  "capture_path":r["path"],
                  "row_path":x.get("path"),
                  "payload":x.get("payload")
                })
    print("CFG",term,json.dumps(out[-80:],ensure_ascii=False)[:70000])
