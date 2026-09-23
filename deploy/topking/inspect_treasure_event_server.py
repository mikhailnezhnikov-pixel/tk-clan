import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,page_text,captured_at
                                        FROM treasure_guide_captures
                                        WHERE source='dom'
                                          AND page_text LIKE '%Линейки наград%'
                                        ORDER BY id""")]

out=[];seen=set()
for r in rows:
    text=re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()
    pos=text.find("Линейки наград")
    if pos<0:continue
    frag=text[pos:pos+1800]
    # Keep only snapshots that look different from the ordinary map view.
    if re.search(r"Получить|Открыть|уров|награ|бесплат|преми|купить|очки|\b1\b.*\b2\b.*\b3\b",frag,re.I):
        key=frag[:900]
        if key in seen:continue
        seen.add(key)
        out.append({"id":r["id"],"captured_at":r["captured_at"],"fragment":frag})
print("ACTIVE_BP_DOM",json.dumps(out[-60:],ensure_ascii=False))
