import importlib.util,re,json
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,page_text,captured_at FROM treasure_guide_captures
                                        WHERE page_text LIKE '%Авторазведка%'
                                           OR page_text LIKE '%Крит. урон%'
                                           OR page_text LIKE '%Вампиризм%'
                                        ORDER BY id DESC LIMIT 60""")]
out=[]
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    out.append({"id":r["id"],"captured_at":r["captured_at"],"text":text[:6000]})
print("MAP_STATS",json.dumps(out,ensure_ascii=False))
