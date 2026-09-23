import importlib.util,re,json
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
names=["Друзья в дорогу","Запас на удачу","Секреты под замком","Золотой урожай"]
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,page_text,assets_json FROM treasure_guide_captures
                                        WHERE page_text<>'' ORDER BY id""")]
out=[]
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    if not any(n in text for n in names):continue
    try:assets=json.loads(r.get("assets_json") or "[]")
    except:assets=[]
    rel=[a for a in assets if re.search(r"shop|bundle|pack|treasure|event_minigame|offer",str(a),re.I)]
    out.append({"id":r["id"],"text":text[-3000:],"assets":rel[-120:]})
print("BUNDLES",json.dumps(out[-40:],ensure_ascii=False))
