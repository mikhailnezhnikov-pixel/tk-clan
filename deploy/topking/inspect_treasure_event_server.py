import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,page_text,captured_at
                                        FROM treasure_guide_captures
                                        WHERE source='dom' AND page_text LIKE '%Поручения питомцам%'
                                        ORDER BY id""")]

out=[]
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    if "Питомцы 5 ур." in text:
        continue
    if "Понятно" in text or "отряд:" in text or re.search(r"\b20\b",text):
        out.append({"id":r["id"],"captured_at":r["captured_at"],"text":text[:5000]})
print("MISSIONS_ALL",json.dumps(out,ensure_ascii=False))
