import importlib.util,json,time

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

now=int(time.time())
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,player_id,source,path,payload_json,page_text,assets_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE source='dom' AND (
                                          page_text LIKE '%Друзья в дорогу%' OR
                                          page_text LIKE '%Запас на удачу%' OR
                                          page_text LIKE '%Секреты под замком%' OR
                                          page_text LIKE '%Золотой урожай%' OR
                                          payload_json LIKE '%bundle_cards%'
                                        )
                                        ORDER BY captured_at DESC,id DESC LIMIT 30""")]

print("NOW",now)
print("SHOP_MATCH_COUNT",len(rows))
for row in rows:
    payload=str(row.get("payload_json") or "")
    page=str(row.get("page_text") or "")
    try:
        obj=json.loads(payload) if payload else {}
    except Exception:
        obj={}
    cards=obj.get("bundle_cards") if isinstance(obj,dict) else None
    print("SHOP_MATCH",json.dumps({
        "id":row.get("id"),
        "player_id":row.get("player_id"),
        "age_s":now-int(row.get("captured_at") or 0),
        "captured_at":row.get("captured_at"),
        "path":row.get("path"),
        "payload_len":len(payload),
        "bundle_card_count":len(cards) if isinstance(cards,list) else None,
        "page_len":len(page),
        "page_has_shop":"Друзья в дорогу" in page,
        "page_head":page[:1600],
        "payload_head":payload[:12000]
    },ensure_ascii=False))
