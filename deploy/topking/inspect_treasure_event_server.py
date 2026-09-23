import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

targets=[
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
"mf_treasurelot_chest_type_015",
"mf_treasurelot_chest_type_02",
"mf_treasurelot_chest_type_03",
"mf_treasurelot_fishing_rod_03_12",
"mf_treasurelot_sword_03_28",
"mf_fair_treasury_room_choose_way_2"
]

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures
                                        WHERE payload_json<>'' ORDER BY id""")]

for term in targets:
    hits=[]
    for r in rows:
        raw=str(r["payload_json"] or "")
        start=0
        while True:
            i=raw.find(term,start)
            if i<0: break
            hits.append({
              "capture":r["id"],"path":r["path"],"pos":i,
              "snippet":raw[max(0,i-900):i+3200]
            })
            start=i+len(term)
            if len(hits)>=12: break
        if len(hits)>=12: break
    print("RAW_TARGET",term,json.dumps(hits,ensure_ascii=False))
