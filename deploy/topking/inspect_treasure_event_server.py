import importlib.util, json
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("SELECT id,path,payload_json FROM treasure_guide_captures WHERE payload_json<>'' ORDER BY id")]

targets=[
 "mf_fairlot_minigame_trader_01_key_uncommon4food",
 "mf_fairlot_minigame_trader_01_food_m",
 "mf_fairlot_minigame_trader_01_verse_gold4food_s",
 "mf_fairlot_minigame_trader_02_expedition_supplies",
 "mf_fairlot_minigame_trader_02_pet_food",
 "mf_fairlot_minigame_trader_02_verse_gold4coins_m",
 "mf_fairlot_minigame_trader_03_map4coins",
 "mf_fairlot_minigame_trader_03_key_uncommon4coins",
 "mf_fairlot_minigame_trader_03_verse_gold4coins",
 "mf_treasurelot_chest_type_015",
 "mf_treasurelot_chest_type_02",
 "mf_treasurelot_chest_type_03",
 "mf_fair_treasury_room_choose_way_2"
]

found={t:[] for t in targets}

def walk(v,target,path="$",depth=0):
    if depth>18:return
    if isinstance(v,dict):
        if str(v.get("id") or "")==target and ("cost" in v or "lot_view" in v or "content_view" in v):
            found[target].append({"json_path":path,"obj":v})
        for k,val in v.items():
            if isinstance(val,(dict,list)): walk(val,target,path+"."+str(k),depth+1)
    elif isinstance(v,list):
        for i,val in enumerate(v[:5000]):
            if isinstance(val,(dict,list)): walk(val,target,path+f"[{i}]",depth+1)

for r in rows:
    try: obj=json.loads(r["payload_json"])
    except: continue
    raw=str(r["payload_json"])
    for t in targets:
        if t not in raw: continue
        before=len(found[t]); walk(obj,t)
        if len(found[t])>before:
            for x in found[t][before:]:
                x["capture"]=r["id"];x["capture_path"]=r["path"]

for t in targets:
    # dedupe serialised objects
    uniq=[];seen=set()
    for x in found[t]:
        key=json.dumps(x["obj"],ensure_ascii=False,sort_keys=True)
        if key in seen:continue
        seen.add(key);uniq.append(x)
    print("OBJ",t,json.dumps(uniq[-8:],ensure_ascii=False)[:30000])
