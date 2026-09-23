import importlib.util,json,time

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

needles=["Друзья в дорогу","Запас на удачу","Секреты под замком","Золотой урожай"]
now=int(time.time())

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE source='api'
                                        ORDER BY captured_at DESC,id DESC LIMIT 800""")]

found=[]
for row in rows:
    payload=str(row.get("payload_json") or "")
    for needle in needles:
        pos=payload.find(needle)
        if pos<0:
            continue
        found.append({
            "capture_id":row.get("id"),
            "api_path":row.get("path"),
            "age_s":now-int(row.get("captured_at") or 0),
            "needle":needle,
            "context":payload[max(0,pos-700):pos+2200]
        })
        break
    if len(found)>=12:
        break

print("TITLE_MATCH_COUNT",len(found))
for item in found:
    print("TITLE_MATCH",json.dumps(item,ensure_ascii=False))
