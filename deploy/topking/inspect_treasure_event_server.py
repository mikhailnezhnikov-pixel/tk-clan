import importlib.util, json, re, time
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

since=int(time.time())-6*3600
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
      SELECT id,path,payload_json,page_text,captured_at
      FROM treasure_guide_captures
      WHERE captured_at>=?
        AND (
          payload_json LIKE '%mf_treasurelot_chest_digging_spot%'
          OR payload_json LIKE '%mf_treasurelot_chest_type_%'
          OR page_text LIKE '%раскоп%'
          OR page_text LIKE '%сундук%'
        )
      ORDER BY id DESC
      LIMIT 1000
    """,(since,))]

print("ROWS",len(rows))
for r in rows[:220]:
    raw=str(r.get("payload_json") or "")
    txt=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    ids=sorted(set(re.findall(r'mf_treasurelot_[a-zA-Z0-9_]+',raw)))
    ids=[x for x in ids if any(k in x for k in ("digging_spot","chest_type","chest_"))]
    if ids:
        print("CAP",r["id"],r["captured_at"],r["path"],json.dumps(ids,ensure_ascii=False))
    if txt and any(k in txt.lower() for k in ("раскоп","сундук","ключ")):
        print("TXT",r["id"],r["captured_at"],r["path"],txt[:8000])
    for term in ("mf_treasurelot_chest_digging_spot","mf_treasurelot_chest_type_015","mf_treasurelot_chest_type_02","mf_treasurelot_chest_type_03"):
        pos=raw.find(term)
        if pos>=0:
            print("RAW",r["id"],term,raw[max(0,pos-3500):pos+12000].replace("\n"," ")[:15500])
