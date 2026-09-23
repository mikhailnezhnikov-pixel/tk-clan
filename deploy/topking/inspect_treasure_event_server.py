import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,page_text,assets_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE source='dom' AND page_text<>''
                                        ORDER BY id""")]

for label in ("Солнечный Лес","Заброшенная Шахта"):
    out=[]
    seen=set()
    for r in rows:
        text=re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()
        if label not in text:continue
        if "МОЖНО ОТЫСКАТЬ" not in text and "СОДЕРЖИТ" not in text:continue
        try:assets=json.loads(r["assets_json"] or "[]")
        except:assets=[]
        rel=[a for a in assets if re.search(r"/items/|treasure_minigame|forest|mine|key_|map_|egg_|berry|skill",str(a),re.I)]
        key=(text[-2200:],tuple(rel))
        if key in seen:continue
        seen.add(key)
        out.append({"id":r["id"],"captured_at":r["captured_at"],"text":text[-3000:],"assets":rel[-160:]})
    print("ROOM",label,json.dumps(out[-40:],ensure_ascii=False))
