import importlib.util,json,time

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

now=int(time.time())
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,source,path,payload_json,page_text,assets_json,captured_at
                                        FROM treasure_guide_captures
                                        ORDER BY id DESC LIMIT 40""")]

print("NOW",now)
print("LATEST_COUNT",len(rows))
for row in rows:
    payload=str(row.get("payload_json") or "")
    page=str(row.get("page_text") or "")
    try:
        assets=json.loads(row.get("assets_json") or "[]")
    except Exception:
        assets=[]
    print("LATEST_CAPTURE",json.dumps({
        "id":row.get("id"),
        "age_s":now-int(row.get("captured_at") or 0),
        "source":row.get("source"),
        "path":row.get("path"),
        "captured_at":row.get("captured_at"),
        "payload_len":len(payload),
        "payload_has_bundle_cards":"bundle_cards" in payload,
        "page_len":len(page),
        "page_has_shop":"Друзья в дорогу" in page,
        "page_head":page[:900],
        "asset_count":len(assets)
    },ensure_ascii=False))
