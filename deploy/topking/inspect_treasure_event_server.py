import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,page_text,assets_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE source='dom' AND page_text LIKE '%Охота за сундуками%'
                                        ORDER BY id""")]

room=[];modal=[];seenr=set();seenm=set()
for r in rows:
    text=re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()
    if "Правила Охота за сундуками" in text:
        key=text[:3000]
        if key not in seenr:
            seenr.add(key);room.append({"id":r["id"],"captured_at":r["captured_at"],"text":text[:5000]})
    if "СОДЕРЖИТ" in text or ("МОЖНО ОТЫСКАТЬ" in text and "Правила Охота за сундуками" in text):
        key=text[-2600:]
        if key not in seenm:
            seenm.add(key);modal.append({"id":r["id"],"captured_at":r["captured_at"],"text":text[-4000:]})
print("ROOM",json.dumps(room[-100:],ensure_ascii=False))
print("MODALS",json.dumps(modal[-100:],ensure_ascii=False))

# Asset deltas around key chest modal transitions.
byid={r["id"]:r for r in rows}
for a,b in [(424,425),(929,930),(990,991),(1017,1018),(558,559)]:
    ra=byid.get(a); rb=byid.get(b)
    if not rb:continue
    try:aa=set(json.loads((ra or {}).get("assets_json") or "[]"))
    except:aa=set()
    try:bb=list(json.loads(rb.get("assets_json") or "[]"))
    except:bb=[]
    delta=[x for x in bb if x not in aa]
    print("DELTA",a,b,json.dumps(delta,ensure_ascii=False))
