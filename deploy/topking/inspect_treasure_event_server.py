import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,source,path,payload_json,page_text,assets_json,captured_at
                                        FROM treasure_guide_captures ORDER BY id""")]

# current client config
cfg_rows=[r for r in rows if r["path"]=="/client_config" and r["payload_json"]]
print("CLIENT_CONFIG_ROWS",len(cfg_rows))
for r in cfg_rows[-2:]:
    try:
        obj=json.loads(r["payload_json"])
    except Exception as e:
        print("CLIENT_CONFIG_PARSE_ERROR",repr(e))
        continue
    print("EVENTS",json.dumps(obj.get("events"),ensure_ascii=False)[:30000])
    treasure_keys=[k for k in obj.keys() if "treasure" in str(k).lower()]
    print("TREASURE_TOP_KEYS",json.dumps(treasure_keys,ensure_ascii=False))
    for k in treasure_keys:
        print("TREASURE_TOP_VALUE",k,json.dumps(obj.get(k),ensure_ascii=False)[:30000])

# compact DOM snapshots grouped by active title.
sections=["Достижения","Задания Сокровищ","Магазин","Питомцы","Поручения питомцам","Линейки наград","Карта Сокровищ"]
for section in sections:
    candidates=[]
    for r in rows:
        text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
        if section not in text:
            continue
        candidates.append((len(text),r["id"],text))
    candidates=sorted(candidates,reverse=True)[:6]
    print("SECTION",section,json.dumps([{"id":i,"text":t[:12000]} for _,i,t in candidates],ensure_ascii=False))

# Relevant asset URLs only.
assets=set()
for r in rows:
    try:
        vals=json.loads(r.get("assets_json") or "[]")
    except Exception:
        vals=[]
    for u in vals:
        u=str(u)
        if re.search(r"treasure|minigames/(?:pets|fishing|chests)|golden_berry",u,re.I):
            assets.add(u)
print("TREASURE_ASSETS",json.dumps(sorted(assets),ensure_ascii=False)[:50000])
