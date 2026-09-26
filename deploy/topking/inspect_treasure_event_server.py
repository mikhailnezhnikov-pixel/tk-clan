import importlib.util, json, re, time
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

since=int(time.time())-6*3600
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
        SELECT id,path,payload_json,page_text,captured_at
        FROM treasure_guide_captures
        WHERE captured_at>=?
        ORDER BY id DESC LIMIT 350
    """,(since,))]

terms=("pet_skill","minigame_pet_skill_","mf_fair_pet_skill_","more_money","more_food",
       "fight_hp_up","fight_treasure_goblin","fight_egg_spawn","fishing_map_finder",
       "chest_finder","chest_map_finder","map_generator","trader_maps","trader_keys","trader_rep")
ru=("Любитель покушать","Охотник за сокровищами","Любитель блестяшек","Боевая кладка",
    "Ключник","Картограф","Карты на прилавке","Рыбацкое чутьё","Любимчик торговцев",
    "Чутьё на сундуки","навык питом")

print("CAPTURES",len(rows))
for r in rows:
    raw=str(r.get("payload_json") or "")
    txt=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    low=(raw+" "+txt).lower()
    if not any(t.lower() in low for t in terms+ru):
        continue
    print("CAP",r["id"],r["captured_at"],r["path"],"payload",len(raw),"text",len(txt))
    if raw:
        try: obj=json.loads(raw)
        except: obj=None
        if isinstance(obj,dict) and isinstance(obj.get("rows"),list):
            for item in obj["rows"]:
                if not isinstance(item,dict): continue
                blob=json.dumps(item,ensure_ascii=False,separators=(",",":"))
                if any(t.lower() in blob.lower() for t in terms+ru):
                    print("ROW",r["id"],blob[:24000])
        # print compact windows around first occurrence of each exact marker
        rawlow=raw.lower()
        for term in terms:
            pos=rawlow.find(term.lower())
            if pos>=0:
                print("RAW",r["id"],term,raw[max(0,pos-700):pos+4200].replace("\n"," ")[:5000])
    if txt:
        txtlow=txt.lower()
        for term in ru:
            pos=txtlow.find(term.lower())
            if pos>=0:
                print("TXT",r["id"],term,txt[max(0,pos-400):pos+1800][:2200])
                break
