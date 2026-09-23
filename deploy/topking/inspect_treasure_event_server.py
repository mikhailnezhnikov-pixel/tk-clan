import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("SELECT id,path,page_text FROM treasure_guide_captures WHERE page_text<>'' ORDER BY id")]

names=["Вареная колбаса","Петрушка","Рыбные консервы","Конфеты","Мясо","Перец","Кукуруза","Яичный порошок","Вареная ветчина","Зеленый горошек","Сухари","Молоко","Молотый кофе","Соль","Морковь"]
for term in names:
    hits=[]
    for r in rows:
        text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
        pos=text.lower().find(term.lower())
        if pos<0: continue
        hits.append({"id":r["id"],"path":r["path"],"snippet":text[max(0,pos-280):pos+650]})
        if len(hits)>=20:break
    print("NAME",term,json.dumps(hits,ensure_ascii=False))
