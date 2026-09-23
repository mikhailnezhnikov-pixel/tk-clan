import importlib.util,json

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,source,path,payload_json,page_text,assets_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE source='dom' AND payload_json LIKE '%bundle_cards%'
                                        ORDER BY id DESC LIMIT 20""")]

print("BUNDLE_CARD_CAPTURE_COUNT",len(rows))
for row in rows[:8]:
    payload=str(row.get("payload_json") or "")
    print("BUNDLE_CARD_CAPTURE",json.dumps({
        "id":row.get("id"),
        "path":row.get("path"),
        "captured_at":row.get("captured_at"),
        "payload":payload[:180000]
    },ensure_ascii=False))
