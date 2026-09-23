import importlib.util,json

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

needles=["cur_hard","item_event_treasure_egg_cradle"]
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE source='api'
                                          AND (path='/client_config' OR path='/items' OR path LIKE '/localization/%')
                                          AND (payload_json LIKE '%cur_hard%' OR payload_json LIKE '%item_event_treasure_egg_cradle%')
                                        ORDER BY captured_at DESC,id DESC LIMIT 80""")]

print("CONFIG_LABEL_ROWS",len(rows))
shown=0
for row in rows:
    payload=str(row.get("payload_json") or "")
    entries=[]
    for needle in needles:
        pos=payload.find(needle)
        if pos>=0:
            entries.append({
                "needle":needle,
                "context":payload[max(0,pos-1800):pos+4200]
            })
    if entries:
        print("CONFIG_LABEL_MATCH",json.dumps({
            "id":row.get("id"),
            "path":row.get("path"),
            "captured_at":row.get("captured_at"),
            "entries":entries
        },ensure_ascii=False))
        shown+=1
        if shown>=12: break
