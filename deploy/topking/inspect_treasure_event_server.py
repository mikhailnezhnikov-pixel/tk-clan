import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("SELECT id,page_text,assets_json FROM treasure_guide_captures WHERE source='dom' ORDER BY id")]
urls=set()
skill_rows=[]
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    try: assets=json.loads(r.get("assets_json") or "[]")
    except: assets=[]
    if "Навык:" in text or "Питомцы 5 ур." in text:
        rel=[a for a in assets if re.search(r"skill|pet|mothcat|fish|goblin|trader|chest|fishing|money|food|map|key",str(a),re.I)]
        if rel:
            skill_rows.append({"id":r["id"],"text":text[-1200:],"assets":rel})
            urls.update(rel)
print("SKILL_ROWS",json.dumps(skill_rows[-80:],ensure_ascii=False))
print("URLS",json.dumps(sorted(urls),ensure_ascii=False))
