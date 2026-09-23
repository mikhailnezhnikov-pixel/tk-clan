import importlib.util, json
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

wanted={
 "mf_fair_treasury_room_choose_way_1",
 "mf_fair_treasury_room_choose_way_2",
 "mf_fair_treasury_room_choose_way_3",
 "mf_treasurelot_chest_type_01",
 "mf_treasurelot_chest_type_015",
 "mf_treasurelot_chest_type_02",
 "mf_treasurelot_chest_type_03",
 "mf_treasurelot_chest_digging_spot_sl4",
 "mf_treasurelot_chest_digging_spot_sl5",
 "mf_treasurelot_chest_digging_spot_sl6",
 "mf_treasurelot_chest_digging_spot_sl7",
 "mf_treasurelot_chest_digging_spot_sl8",
 "mf_treasurelot_chest_digging_spot_sl9"
}
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE path LIKE '/shop/view#treasure-%'
                                        ORDER BY id DESC LIMIT 40""")]
print("META",json.dumps([{"id":r["id"],"path":r["path"],"captured_at":r["captured_at"]} for r in rows],ensure_ascii=False))
found=[]
for r in rows:
    try:obj=json.loads(r["payload_json"])
    except:continue
    for x in obj.get("rows",[]) if isinstance(obj,dict) else []:
        if not isinstance(x,dict):continue
        p=x.get("payload")
        if not isinstance(p,dict):continue
        pid=str(p.get("id") or "")
        if pid in wanted:
            found.append({"capture":r["id"],"row_path":x.get("path"),"payload":p})
print("PRIORITY",json.dumps(found,ensure_ascii=False))
