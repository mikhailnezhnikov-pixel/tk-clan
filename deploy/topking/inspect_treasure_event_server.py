import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

titles=[
"Красная жатва I","Синяя жатва III","Да он только крепче стал!","Это вышло из-под контроля",
"Абсолютная единица","Чистая работа III","Кто там, в глубине?","Хватка глубин I",
"Вода успокоилась","Крупная находка","Нашёл выход","Бартерщик","Редкая связка",
"Искатель сокровищ II","Искатель сокровищ VI","Глубже в горы I","Глубже в горы III",
"Землекоп II","Землекоп III","Навстречу шторму III","Не заблудился"
]
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("SELECT id,path,payload_json FROM treasure_guide_captures WHERE payload_json<>'' ORDER BY id")]

for title in titles:
    hits=[]
    for r in rows:
        raw=str(r["payload_json"] or "")
        pos=raw.find(title)
        if pos<0:continue
        hits.append({"id":r["id"],"path":r["path"],"snippet":raw[max(0,pos-500):pos+900]})
        if len(hits)>=5:break
    print("TITLE",title,json.dumps(hits,ensure_ascii=False))
