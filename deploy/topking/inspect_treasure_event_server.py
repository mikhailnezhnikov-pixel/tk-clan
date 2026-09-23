import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,page_text,assets_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE source='dom' AND page_text LIKE '%Линейки наград%'
                                        ORDER BY id""")]

out=[];seen=set()
for r in rows:
    text=re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()
    if not text:continue
    # prefer snapshots where the reward track itself is likely open
    score=0
    for term in ("Награда","Получить","ур.","уров","Бесплат","Преми","Очки события","Линейки наград"):
        if term.lower() in text.lower():score+=1
    if score<2:continue
    key=text[:3500]
    if key in seen:continue
    seen.add(key)
    try:assets=json.loads(r["assets_json"] or "[]")
    except:assets=[]
    rel=[a for a in assets if re.search(r"battle_pass|bp_event_minigame|treasurehunt_|egg_|key_|map_|skill_change|cur_gold",str(a),re.I)]
    out.append({"id":r["id"],"captured_at":r["captured_at"],"text":text[:9000],"assets":rel[-180:]})
print("TRACK_DOM",json.dumps(out[-100:],ensure_ascii=False))
