import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,page_text,assets_json FROM treasure_guide_captures
                                        WHERE source='dom' AND page_text LIKE '%Друзья в дорогу%'
                                        ORDER BY id DESC LIMIT 8""")]
out=[]
for r in rows:
    text=re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()
    try:assets=json.loads(r["assets_json"] or "[]")
    except:assets=[]
    rel=[]
    for idx,a in enumerate(assets):
        s=str(a)
        if re.search(r"/items/|/currencies/",s,re.I):
            if re.search(r"treasure|pet|gold|prem|hard|map_|key_|berry|skill_change|energy|food",s,re.I):
                rel.append({"i":idx,"url":s})
    out.append({"id":r["id"],"text":text[-2200:],"ordered_assets":rel})
print("SHOP_ORDER",json.dumps(out,ensure_ascii=False))
