import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,page_text,assets_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE source='dom'
                                          AND (page_text LIKE '%Солнечный Лес%'
                                               OR page_text LIKE '%Заброшенная Шахта%'
                                               OR page_text LIKE '%Лес%'
                                               OR page_text LIKE '%Шахт%')
                                        ORDER BY id""")]

out=[];seen=set()
for r in rows:
    text=re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()
    if not text:continue
    if not ("Солнечный Лес" in text or "Заброшенная Шахта" in text or "Правила" in text):continue
    key=text[:4500]
    if key in seen:continue
    seen.add(key)
    try:assets=json.loads(r["assets_json"] or "[]")
    except:assets=[]
    rel=[a for a in assets if re.search(r"forest|mine|greed|treasure|minigame|item_",str(a),re.I)]
    out.append({"id":r["id"],"captured_at":r["captured_at"],"text":text[:6500],"assets":rel[-140:]})
print("FOREST_MINE",json.dumps(out,ensure_ascii=False))
