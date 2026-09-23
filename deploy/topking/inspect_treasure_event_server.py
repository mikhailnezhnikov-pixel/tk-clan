import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

patterns=[
 "attack","speed","health","move","crit","dodge","block","vamp",
 "double","reward","treasurehunt_stat","minigame_stat","icon_stat"
]
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("SELECT assets_json FROM treasure_guide_captures WHERE assets_json<>''")]

urls=set()
for r in rows:
    try:arr=json.loads(r["assets_json"] or "[]")
    except:continue
    for a in arr:
        s=str(a)
        low=s.lower()
        if any(p in low for p in patterns):
            if re.search(r"minigame|treasure|stat|fight|icon",low):
                urls.add(s)
print("STAT_ASSETS",json.dumps(sorted(urls),ensure_ascii=False))
