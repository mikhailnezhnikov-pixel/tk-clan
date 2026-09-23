import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("SELECT id,path,payload_json,page_text FROM treasure_guide_captures ORDER BY id")]

ids=[f"item_{kind}_t{n}" for n in range(1,6) for kind in ("box","food","water")]
names=["Вареная колбаса","Петрушка","Рыбные консервы","Конфеты","Мясо","Перец","Кукуруза","Яичный порошок","Вареная ветчина","Зеленый горошек","Сухари","Молоко","Молотый кофе","Соль","Морковь"]

for term in ids+names:
    hits=[]
    rx=re.compile(re.escape(term),re.I)
    for r in rows:
        for field in ("payload_json","page_text"):
            txt=str(r.get(field) or "")
            m=rx.search(txt)
            if not m: continue
            hits.append({"id":r["id"],"path":r["path"],"field":field,"snippet":txt[max(0,m.start()-500):m.end()+1200]})
            if len(hits)>=12: break
        if len(hits)>=12: break
    print("TERM",term,json.dumps(hits,ensure_ascii=False))
