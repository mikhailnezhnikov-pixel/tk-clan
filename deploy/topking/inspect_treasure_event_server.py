import importlib.util, json
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

targets=[
 "mf_fair_treasury_room_choose_way_1",
 "mf_fair_treasury_room_choose_way_2",
 "mf_fair_treasury_room_choose_way_3",
 "mf_treasurelot_chest_type_01",
 "mf_treasurelot_chest_type_015",
 "mf_treasurelot_chest_type_02",
 "mf_treasurelot_chest_type_03"
]
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures
                                        WHERE path LIKE '/shop/view#treasure-%'
                                        ORDER BY id""")]

for t in targets:
    out=[]
    for r in rows:
        try:obj=json.loads(r["payload_json"])
        except:continue
        for x in obj.get("rows",[]) if isinstance(obj,dict) else []:
            if not isinstance(x,dict):continue
            blob=json.dumps(x,ensure_ascii=False,separators=(",",":"))
            if t in blob:
                out.append({"capture":r["id"],"capture_path":r["path"],"row_path":x.get("path"),"payload":x.get("payload")})
    print("SEL",t,json.dumps(out[-40:],ensure_ascii=False)[:60000])
