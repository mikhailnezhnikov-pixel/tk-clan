import importlib.util,json
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    r=db.execute("""SELECT id,source,path,payload_json,page_text,assets_json,captured_at
                    FROM treasure_guide_captures
                    WHERE source='dom' AND page_text LIKE '%Друзья в дорогу%'
                    ORDER BY id DESC LIMIT 1""").fetchone()
    if not r:
        raise SystemExit("SHOP_DOM_CAPTURE_MISSING")

    row=dict(r)
    assets=json.loads(row.get("assets_json") or "[]")
    page_text=str(row.get("page_text") or "")
    payload_text=str(row.get("payload_json") or "")

    print("SHOP_CAPTURE_META",json.dumps({
        "id":row.get("id"),
        "source":row.get("source"),
        "path":row.get("path"),
        "captured_at":row.get("captured_at"),
        "page_text_len":len(page_text),
        "payload_len":len(payload_text),
        "asset_count":len(assets)
    },ensure_ascii=False))

    print("SHOP_PAGE_TEXT",json.dumps(page_text[:50000],ensure_ascii=False))
    print("SHOP_PAYLOAD",payload_text[:70000])

    window=[{"i":i,"url":assets[i]} for i in range(min(0,len(assets)),min(80,len(assets)))]
    print("SHOP_ASSETS",json.dumps(window,ensure_ascii=False))
