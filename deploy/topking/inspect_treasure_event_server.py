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

out=[];seen=set()
for r in rows:
    text=re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()
    if not re.search(r"Т[её]мн.*пакт|Светл.*пакт|боев.*пропуск|Линейки наград",text,re.I):continue
    # keep screens that look closer to BP than ordinary nav-only pages
    if len(text)<80:continue
    key=text[:4500]
    if key in seen:continue
    seen.add(key)
    try:assets=json.loads(r["assets_json"] or "[]")
    except:assets=[]
    rel=[a for a in assets if re.search(r"battle_pass|bp_event_minigame|golden_berry|treasurehunt_|egg_|key_|map_|skill_change|cur_gold",str(a),re.I)]
    out.append({"id":r["id"],"captured_at":r["captured_at"],"text":text[:10000],"assets":rel[-220:]})
print("PACT_SCREENS",json.dumps(out[-120:],ensure_ascii=False))
