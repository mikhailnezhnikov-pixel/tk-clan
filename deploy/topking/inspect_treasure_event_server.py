import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,page_text FROM treasure_guide_captures
                                        WHERE page_text<>'' ORDER BY id""")]

for label in ["Тайный Торговец","Сокровищница","Рыбалка","Сражение","Лабиринт","Сундук"]:
    seen=set(); out=[]
    for r in rows:
        text=re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()
        if label.lower() not in text.lower(): continue
        # keep only tail after last HK marker to focus opened modal/minigame
        pos=text.rfind(" HK ")
        tail=text[pos+4:] if pos>=0 else text
        sig=tail[:500]
        if sig in seen: continue
        seen.add(sig)
        out.append({"id":r["id"],"path":r["path"],"tail":tail[:2800]})
    print("SCREEN_GROUP",label,json.dumps(out[:40],ensure_ascii=False))
