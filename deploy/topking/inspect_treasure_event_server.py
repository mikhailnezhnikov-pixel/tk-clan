import importlib.util, json, re, time
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
      SELECT id,path,page_text,assets_json,captured_at
      FROM treasure_guide_captures
      WHERE source='dom' AND captured_at>=?
      ORDER BY id DESC LIMIT 1200
    """,(int(time.time())-72*3600,))]
urls={}
for r in rows:
    try: assets=json.loads(r.get("assets_json") or "[]")
    except: assets=[]
    for a in assets:
        s=str(a)
        if re.search(r"skill_(?:fight_hp_up|chest_map_finder|more_food|more_money|chest_finder|trader_rep|fishing_map_finder)",s,re.I):
            urls.setdefault(s,[]).append(r["id"])
print("ASSETS",json.dumps([{"url":k,"captures":v[-10:]} for k,v in sorted(urls.items())],ensure_ascii=False))
