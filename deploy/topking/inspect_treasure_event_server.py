import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,page_text,assets_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE source='dom'
                                          AND (page_text LIKE '%Солнечный Лес%' OR page_text LIKE '%Заброшенная Шахта%')
                                        ORDER BY id""")]

out=[]
seen=set()
for r in rows:
    text=re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()
    if "МОЖНО ОТЫСКАТЬ" not in text and "МОЖНО НАЙТИ" not in text: continue
    name="Солнечный Лес" if "Солнечный Лес" in text else "Заброшенная Шахта"
    pos=text.find(name)
    clip=text[pos:pos+900] if pos>=0 else text[:900]
    key=(name,clip)
    if key in seen: continue
    seen.add(key)
    try:assets=json.loads(r["assets_json"] or "[]")
    except:assets=[]
    rel=[]
    for a in assets:
        s=str(a)
        if re.search(r"item_treasurehunt_(?:cur_coins|energy|pet_food|pet_skill_change|key_)|item_event_treasure_golden_berry|item_pet_(?:fish|mothcat)_egg_",s,re.I):
            rel.append(s)
    out.append({"id":r["id"],"name":name,"text":clip,"assets":sorted(set(rel))})
print("ROOM_CARDS",json.dumps(out[-30:],ensure_ascii=False))
