import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,page_text FROM treasure_guide_captures
                                        WHERE page_text<>'' ORDER BY id""")]

terms=[
 "Провизия","Удочка","удочка","Меч","меч","Рыбалка","Сражение",
 "Торговец","Сундук","сундук","Лабиринт","Сокровищница","навык","Навык",
 "Золотую Ягоду","ключ","Ключ"
]
for term in terms:
    hits=[]
    for r in rows:
        text=re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()
        start=0
        while True:
            i=text.lower().find(term.lower(),start)
            if i<0: break
            hits.append({"id":r["id"],"path":r["path"],"snippet":text[max(0,i-260):i+900]})
            start=i+len(term)
            if len(hits)>=35: break
        if len(hits)>=35: break
    print("TERM",term,json.dumps(hits,ensure_ascii=False))
