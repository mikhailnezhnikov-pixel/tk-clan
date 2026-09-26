import importlib.util, json, re, time
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

since=int(time.time())-12*3600
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
      SELECT id,path,page_text,captured_at
      FROM treasure_guide_captures
      WHERE captured_at>=? AND page_text LIKE '%Навык:%'
      ORDER BY id DESC
      LIMIT 500
    """,(since,))]
print("SKILL_DOM_COUNT",len(rows))
for r in rows:
    txt=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    pos=txt.find("Навык:")
    if pos<0: continue
    print("SKILLDOM",r["id"],r["captured_at"],r["path"],txt[max(0,pos-80):pos+1700])
