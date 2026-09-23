import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

patterns=[
 ("fishing",r"заброс|Рыбалк|водоём"),
 ("lights",r"Ламп|Лабиринт|Lights"),
 ("fight",r"Сражени|красн|син|зелён")
]
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,page_text,assets_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE source='dom' AND page_text<>''
                                        ORDER BY id""")]
for label,pat in patterns:
    rx=re.compile(pat,re.I)
    found=[]
    for idx,r in enumerate(rows):
        text=re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()
        if not rx.search(text):continue
        if len(text)>6500:continue
        try:cur=set(json.loads(r["assets_json"] or "[]"))
        except:cur=set()
        old=set()
        if idx>0:
            try:old=set(json.loads(rows[idx-1]["assets_json"] or "[]"))
            except:old=set()
        delta=[x for x in sorted(cur-old) if re.search(r"minigames/(?:fishing|lights|fight)|/items/|/currencies/",x,re.I)]
        rel=[x for x in sorted(cur) if re.search(r"minigames/(?:fishing|lights|fight)|/items/item_treasurehunt|/items/item_event_treasure",x,re.I)]
        found.append({"id":r["id"],"text":text[-1800:],"delta":delta,"rel":rel[-80:]})
    print("ACTION",label,json.dumps(found[-30:],ensure_ascii=False))
