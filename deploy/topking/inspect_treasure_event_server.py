import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,page_text,assets_json,captured_at
                                        FROM treasure_guide_captures ORDER BY id""")]

bp=[{"id":r["id"],"path":r["path"],"captured_at":r["captured_at"],"payload":str(r["payload_json"] or "")[:22000]}
    for r in rows if str(r["path"]).startswith("/battlepass")]
print("BATTLEPASS_ROWS",json.dumps(bp[-80:],ensure_ascii=False))

dom=[];seen=set()
for r in rows:
    text=re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()
    if "Линейки наград" not in text:continue
    if "Достижения" in text and len(text)>8000:continue
    key=text[:5000]
    if key in seen:continue
    seen.add(key)
    try:assets=json.loads(r["assets_json"] or "[]")
    except:assets=[]
    rel=[a for a in assets if re.search(r"battle_pass|reward|treasurehunt_|egg_|key_|map_|skill_change",str(a),re.I)]
    dom.append({"id":r["id"],"captured_at":r["captured_at"],"text":text[:7000],"assets":rel[-160:]})
print("BATTLEPASS_DOM",json.dumps(dom[-80:],ensure_ascii=False))
