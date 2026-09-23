import importlib.util, json, re, os, glob

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    tables=[x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    print("TABLES",json.dumps(tables,ensure_ascii=False))
    rows=[dict(r) for r in db.execute("""SELECT id,source,path,payload_json,page_text,assets_json,captured_at
                                        FROM treasure_guide_captures ORDER BY id""")]

for target in ["/shop/view","/quests","/client_config","/fair/reroll","/shop/buy","/battlepass/claim","/quest/claim"]:
    subset=[r for r in rows if r["path"]==target]
    print("PATH",target,"COUNT",len(subset))
    for r in subset[-4:]:
        p=str(r["payload_json"] or "")
        valid=True
        try: obj=json.loads(p)
        except Exception as e: valid=False; obj=None
        print("PAYLOAD_META",json.dumps({"id":r["id"],"path":target,"len":len(p),"valid_json":valid,"head":p[:250],"tail":p[-250:]},ensure_ascii=False))
        if valid and isinstance(obj,dict):
            print("TOP_KEYS",r["id"],json.dumps(list(obj.keys())[:100],ensure_ascii=False))

# Search raw captured payloads for known treasure lot ids and print surrounding text.
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
    hits=[]
    for r in rows:
        p=str(r["payload_json"] or "")
        i=p.find(term)
        if i>=0:
            hits.append({"id":r["id"],"path":r["path"],"snippet":p[max(0,i-1200):i+5000]})
    print("TERM_HITS",term,json.dumps(hits[-5:],ensure_ascii=False)[:45000])

# Inspect possible static snapshot/cache files on disk.
paths=[]
for base in ["/opt/hamsterking-license","/var/lib/hamsterking-license","/opt"]:
    if not os.path.exists(base): continue
    for pat in ["**/*static*","**/*document*","**/*client_config*","**/*shop*json","**/*items*json","**/*events*json"]:
        for p in glob.glob(os.path.join(base,pat),recursive=True):
            try:
                if os.path.isfile(p) and os.path.getsize(p)<50_000_000:
                    paths.append({"path":p,"size":os.path.getsize(p)})
            except: pass
print("CACHE_FILES",json.dumps(paths[:300],ensure_ascii=False))
