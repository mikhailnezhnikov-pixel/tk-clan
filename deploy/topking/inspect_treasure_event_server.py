import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

titles=["Солнечный Лес","Заброшенная Шахта","Необычный Водоём","Тайный Торговец","Охота за сундуками","Сражение","Лабиринт","Сокровищница"]
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,page_text,captured_at
                                        FROM treasure_guide_captures
                                        WHERE source='dom' AND page_text LIKE '%МОЖНО ОТЫСКАТЬ%'
                                        ORDER BY id""")]

for title in titles:
    vals=[];seen=set()
    for r in rows:
        text=re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()
        pos=text.find(title)
        if pos<0:continue
        seg=text[pos:pos+1800]
        hk=seg.find(" HK")
        if hk>0:seg=seg[:hk]
        if "МОЖНО ОТЫСКАТЬ" not in seg:continue
        nums=re.findall(r"(?<![A-Za-zА-Яа-я])\d+(?![A-Za-zА-Яа-я])",seg)
        key=seg[:1200]
        if key in seen:continue
        seen.add(key)
        vals.append({"id":r["id"],"captured_at":r["captured_at"],"last_number":nums[-1] if nums else None,"segment":seg})
    print("ROOM",title,json.dumps(vals[-12:],ensure_ascii=False))
