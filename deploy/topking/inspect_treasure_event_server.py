import importlib.util,json,time

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

now=int(time.time())
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,page_text,captured_at
                                        FROM treasure_guide_captures
                                        WHERE source='dom'
                                        ORDER BY captured_at DESC,id DESC LIMIT 500""")]

with_payload=[]
for row in rows:
    payload=str(row.get("payload_json") or "")
    if payload:
        with_payload.append({
            "id":row.get("id"),
            "age_s":now-int(row.get("captured_at") or 0),
            "path":row.get("path"),
            "payload_len":len(payload),
            "has_bundle_cards":"bundle_cards" in payload,
            "page_head":str(row.get("page_text") or "")[:260]
        })
        if len(with_payload)>=30:
            break

print("DOM_ROWS_SCANNED",len(rows))
print("DOM_WITH_PAYLOAD_COUNT",len(with_payload))
for item in with_payload:
    print("DOM_WITH_PAYLOAD",json.dumps(item,ensure_ascii=False))
