import importlib.util, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
      SELECT id,path,page_text,captured_at
      FROM treasure_guide_captures
      WHERE page_text LIKE '%Навык:%'
      ORDER BY id DESC
      LIMIT 3000
    """)]
print("ALL_SKILL_DOM_COUNT",len(rows))
seen=set()
for r in rows:
    txt=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    pos=txt.find("Навык:")
    if pos<0: continue
    snippet=txt[max(0,pos-100):pos+1900]
    # de-duplicate identical modal text while preserving first/newest source id.
    key=re.sub(r"^.*?Навык:","Навык:",snippet)
    if key in seen: continue
    seen.add(key)
    print("SKILLDOM",r["id"],r["captured_at"],r["path"],snippet)
