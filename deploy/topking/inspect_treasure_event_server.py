import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    matches=[dict(r) for r in db.execute("""SELECT id,page_text,assets_json,captured_at FROM treasure_guide_captures
                                           WHERE source='dom' AND page_text<>''
                                             AND (page_text LIKE '%Солнечный Лес%' OR page_text LIKE '%Заброшенная Шахта%')
                                             AND page_text LIKE '%МОЖНО ОТЫСКАТЬ%'
                                           ORDER BY id DESC LIMIT 20""")]
    out=[]
    for r in matches:
        prev=db.execute("""SELECT id,assets_json,page_text FROM treasure_guide_captures
                           WHERE source='dom' AND id<? ORDER BY id DESC LIMIT 1""",(r["id"],)).fetchone()
        try:cur=set(json.loads(r["assets_json"] or "[]"))
        except:cur=set()
        try:old=set(json.loads(prev["assets_json"] or "[]")) if prev else set()
        except:old=set()
        delta=[x for x in sorted(cur-old) if re.search(r"/items/|/currencies/|key_|map_|egg_|berry|skill_change|pet_food|treasurehunt_",x,re.I)]
        text=re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()
        label="Солнечный Лес" if "Солнечный Лес" in text else "Заброшенная Шахта"
        out.append({"id":r["id"],"prev":prev["id"] if prev else None,"label":label,"text":text[-800:],"delta":delta})
print("ROOM_DELTAS",json.dumps(out,ensure_ascii=False))
