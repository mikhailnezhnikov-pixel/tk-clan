import importlib.util, json

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

targets={
"mf_fair_treasury_room_choose_way_1",
"mf_fair_treasury_room_choose_way_2",
"mf_fair_treasury_room_choose_way_3",
"mf_treasurelot_chest_type_015",
"mf_treasurelot_chest_type_02",
"mf_treasurelot_chest_type_03",
"mf_fairlot_minigame_trader_02_expedition_supplies",
"mf_fairlot_minigame_trader_02_pet_food",
"mf_fairlot_minigame_trader_02_mothcat_egg_01",
"mf_fairlot_minigame_trader_02_mothcat_egg_02",
"mf_fairlot_minigame_trader_02_mothcat_egg_06",
"mf_fairlot_minigame_trader_02_verse_gold4coins_m",
"mf_fairlot_minigame_trader_02_verse_gold4coins_l",
"mf_fairlot_minigame_trader_03_map4coins",
"mf_fair_pet_skill_more_money_r4",
"mf_fair_pet_skill_more_food_r4",
"mf_fair_pet_skill_trader_keys_r4",
"mf_fair_pet_skill_fight_hp_up_r4",
"mf_fair_pet_skill_treasure_goblin_r4",
"mf_fair_pet_skill_fishing_map_finder_r4",
"mf_treasurelot_fishing_rod_03_12",
"mf_treasurelot_sword_03_28"
}

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures
                                        WHERE path LIKE '%#treasure-%'
                                        ORDER BY id""")]

found={}
def walk(v,src,path="$"):
    if isinstance(v,dict):
        oid=str(v.get("id") or "")
        if oid in targets and oid not in found:
            found[oid]={"capture":src["id"],"source_path":src["path"],"json_path":path,"object":v}
        for k,val in v.items():
            if isinstance(val,(dict,list)): walk(val,src,path+"."+str(k))
    elif isinstance(v,list):
        for i,val in enumerate(v):
            if isinstance(val,(dict,list)): walk(val,src,path+f"[{i}]")

for r in rows:
    try: obj=json.loads(r["payload_json"] or "{}")
    except: continue
    walk(obj,r)

for tid in sorted(targets):
    print("EXACT_TARGET",tid,json.dumps(found.get(tid),ensure_ascii=False,separators=(",",":")))
