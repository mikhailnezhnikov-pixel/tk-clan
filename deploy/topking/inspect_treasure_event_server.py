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

out=[];seen=set()
for r in rows:
    text=re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()
    if "МОЖНО ОТЫСКАТЬ" not in text:continue
    # modal tail beginning with account count immediately before title
    pos=text.rfind("Охота за сундуками")
    tail=text[max(0,pos-30):pos+2600]
    if tail in seen:continue
    seen.add(tail)
    try:assets=json.loads(r["assets_json"] or "[]")
    except:assets=[]
    chest_assets=[a for a in assets if re.search(r"chest|digging|treasure_minigame_chest",str(a),re.I)]
    out.append({"id":r["id"],"captured_at":r["captured_at"],"text":tail,"assets":chest_assets})
print("CHEST_CARDS",json.dumps(out,ensure_ascii=False))

# exact-id string occurrence in all payloads
targets=["mf_treasurelot_chest_type_01","mf_treasurelot_chest_type_015","mf_treasurelot_chest_type_02","mf_treasurelot_chest_type_03","mf_fair_treasury_room_choose_way_2"]
with server.db_session() as db:
    prows=[dict(r) for r in db.execute("SELECT id,path,payload_json FROM treasure_guide_captures WHERE payload_json<>'' ORDER BY id")]
for t in targets:
    needle='"id":"'+t+'"'
    hits=[]
    for r in prows:
        raw=str(r["payload_json"] or "")
        start=0
        while True:
            pos=raw.find(needle,start)
            if pos<0:break
            hits.append({"id":r["id"],"path":r["path"],"snippet":raw[max(0,pos-1200):pos+6000]})
            start=pos+len(needle)
            if len(hits)>=20:break
        if len(hits)>=20:break
    print("IDOBJ",t,json.dumps(hits,ensure_ascii=False))
