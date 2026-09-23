import importlib.util,json

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

needles=["cur_hard","item_event_treasure_egg_cradle"]
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,source,path,payload_json,page_text,captured_at
                                        FROM treasure_guide_captures
                                        WHERE payload_json LIKE '%cur_hard%'
                                           OR payload_json LIKE '%item_event_treasure_egg_cradle%'
                                           OR page_text LIKE '%cur_hard%'
                                           OR page_text LIKE '%egg_cradle%'
                                        ORDER BY captured_at DESC,id DESC LIMIT 120""")]

print("TARGET_MATCH_ROWS",len(rows))
out=0
for row in rows:
    payload=str(row.get("payload_json") or "")
    page=str(row.get("page_text") or "")
    snippets=[]
    for needle in needles:
        for source_name,text_value in [("payload",payload),("page",page)]:
            pos=text_value.find(needle)
            if pos>=0:
                snippets.append({
                    "needle":needle,
                    "source":source_name,
                    "context":text_value[max(0,pos-900):pos+2600]
                })
    if snippets:
        print("TARGET_MATCH",json.dumps({
            "id":row.get("id"),
            "source":row.get("source"),
            "path":row.get("path"),
            "captured_at":row.get("captured_at"),
            "snippets":snippets[:4]
        },ensure_ascii=False))
        out+=1
        if out>=20: break
