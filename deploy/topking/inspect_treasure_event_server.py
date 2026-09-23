import importlib.util,json
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    r=db.execute("""SELECT id,page_text,assets_json FROM treasure_guide_captures
                    WHERE source='dom' AND page_text LIKE '%Друзья в дорогу%'
                    ORDER BY id DESC LIMIT 1""").fetchone()
assets=json.loads(r["assets_json"] or "[]")
window=[{"i":i,"url":assets[i]} for i in range(min(15,len(assets)),min(50,len(assets)))]
print("SHOP_ASSET_WINDOW",json.dumps(window,ensure_ascii=False))
