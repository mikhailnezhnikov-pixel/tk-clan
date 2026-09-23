import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures ORDER BY id""")]

shop=next((str(r["payload_json"] or "") for r in rows if r["path"]=="/shop/view"),"")
print("SHOP_LEN",len(shop))
for key in ['"shop_lots"', '"shopLots"', '"lots"', '"fairs"', '"offers"', '"content_view"', '"cost"', '"costs"']:
    pos=shop.find(key)
    print("SHOP_KEY",key,pos, shop[max(0,pos-200):pos+1000] if pos>=0 else "")

terms=[
 "mf_fair_treasury_room_choose_way_1",
 "mf_fair_treasury_room_choose_way_2",
 "mf_fair_treasury_room_choose_way_3",
 "mf_treasurelot_chest_type_015",
 "mf_treasurelot_chest_type_02",
 "mf_treasurelot_chest_type_03",
 "mf_treasurelot_trader_type_03_active_rep_5",
 "mf_fairlot_minigame_trader_03_map4coins",
 "mf_fair_pet_skill_more_money_r4",
 "mf_fair_pet_skill_more_food_r4",
 "mf_fair_pet_skill_trader_keys_r4",
 "mf_fair_pet_skill_fight_hp_up_r4",
 "mf_fair_pet_skill_treasure_goblin_r4",
 "mf_treasurelot_fishing_rod_03_12",
 "mf_treasurelot_sword_03_28",
]
for term in terms:
    pos=shop.find(term)
    print("SHOP_TERM",term,pos)
    if pos>=0:
        print("SHOP_SNIP",term,shop[max(0,pos-900):pos+2200])

# Look for exact lot ids in any VALID JSON response and recursively show the containing object.
valid_rows=[]
for r in rows:
    p=str(r["payload_json"] or "")
    try: obj=json.loads(p)
    except: continue
    valid_rows.append((r["id"],r["path"],obj))

def find_objects(v,term,path="$",out=None,depth=0):
    if out is None: out=[]
    if depth>12 or len(out)>=20:return out
    if isinstance(v,dict):
        try: blob=json.dumps(v,ensure_ascii=False,separators=(",",":"))
        except: blob=""
        if term in blob and len(blob)<=12000:
            out.append((path,v))
            return out
        for k,val in v.items():
            if isinstance(val,(dict,list)): find_objects(val,term,path+"."+str(k),out,depth+1)
    elif isinstance(v,list):
        for i,val in enumerate(v[:2000]):
            if isinstance(val,(dict,list)): find_objects(val,term,path+f"[{i}]",out,depth+1)
    return out

for term in terms:
    found=[]
    for rid,path,obj in valid_rows:
        hits=find_objects(obj,term)
        for hp,hv in hits[:3]:
            found.append({"capture":rid,"path":path,"json_path":hp,"obj":hv})
        if len(found)>=5:break
    print("VALID_TERM",term,json.dumps(found,ensure_ascii=False)[:20000])
