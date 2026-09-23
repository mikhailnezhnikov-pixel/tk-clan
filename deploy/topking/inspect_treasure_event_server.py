import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,page_text,assets_json FROM treasure_guide_captures
                                        WHERE source='dom' AND page_text<>''
                                        ORDER BY id""")]

titles=[
"Красная жатва I","Синяя жатва III","Да он только крепче стал!","Это вышло из-под контроля",
"Абсолютная единица","Чистая работа III","Кто там, в глубине?","Хватка глубин I",
"Вода успокоилась","Крупная находка","Нашёл выход","Бартерщик","Редкая связка",
"Искатель сокровищ II","Искатель сокровищ VI","Глубже в горы I","Глубже в горы III",
"Землекоп II","Землекоп III","Навстречу шторму III","Не заблудился"
]

for title in titles:
    hits=[]
    for r in rows:
        text=re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()
        if title not in text: continue
        try: assets=json.loads(r["assets_json"] or "[]")
        except: assets=[]
        rel=[a for a in assets if re.search(r"achievement|reward|event_minigame|treasurehunt_|minigame_(?:fight|fishing|chests|trader|lights)|key_|egg_|map_",str(a),re.I)]
        hits.append({"id":r["id"],"text":text[-1800:],"assets":rel[-120:]})
    print("ACH",title,json.dumps(hits[-6:],ensure_ascii=False))

# all achievement-like art URLs
all_urls=set()
for r in rows:
    try: assets=json.loads(r["assets_json"] or "[]")
    except: continue
    for a in assets:
        if re.search(r"achievement",str(a),re.I):
            all_urls.add(str(a))
print("ACH_URLS",json.dumps(sorted(all_urls),ensure_ascii=False))
