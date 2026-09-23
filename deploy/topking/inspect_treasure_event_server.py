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
 "mf_treasurelot_chest_type_03",
 "mf_treasurelot_chest_digging_spot_sl4",
 "mf_treasurelot_chest_digging_spot_sl5",
 "mf_treasurelot_chest_digging_spot_sl6",
 "mf_treasurelot_chest_digging_spot_sl7",
 "mf_treasurelot_chest_digging_spot_sl8",
 "mf_treasurelot_chest_digging_spot_sl9"
]

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures
                                        WHERE path IN ('/shop/buy','/fair/reroll') AND payload_json<>''
                                        ORDER BY id DESC LIMIT 180""")]

found={t:[] for t in targets}
def walk(v,capture,cpath,path="$",depth=0):
    if depth>18:return
    if isinstance(v,dict):
        oid=str(v.get("id") or "")
        if oid in found:
            found[oid].append({"capture":capture,"capture_path":cpath,"json_path":path,"obj":v})
        for k,val in v.items():
            if isinstance(val,(dict,list)):walk(val,capture,cpath,path+"."+str(k),depth+1)
    elif isinstance(v,list):
        for i,val in enumerate(v[:12000]):
            if isinstance(val,(dict,list)):walk(val,capture,cpath,path+f"[{i}]",depth+1)

for r in rows:
    try:obj=json.loads(r["payload_json"])
    except:continue
    walk(obj,r["id"],r["path"])

for t in targets:
    uniq=[];seen=set()
    for x in found[t]:
        key=json.dumps(x["obj"],ensure_ascii=False,sort_keys=True)
        if key in seen:continue
        seen.add(key);uniq.append(x)
    print("EXACT",t,json.dumps(uniq[-12:],ensure_ascii=False)[:50000])
