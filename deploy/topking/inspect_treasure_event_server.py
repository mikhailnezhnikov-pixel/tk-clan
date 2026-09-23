import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,page_text,captured_at
                                        FROM treasure_guide_captures
                                        WHERE source='dom' AND id>=1040
                                        ORDER BY id""")]

skills=[]
missions=[]
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    if not text:
        continue
    m=re.search(r"\[(B|A|S|S\+)\]\s*Навык:\s*([^⚡]+?)\s*⚡️(.*?)(?:⚠️|Понятно|$)",text)
    if m:
        skills.append({
          "id":r["id"],"rank":m.group(1),"title":m.group(2).strip(),"effect":m.group(3).strip()
        })
    if "Поручения питомцам" in text and "Питомцы 5 ур." not in text:
        missions.append({"id":r["id"],"captured_at":r["captured_at"],"text":text[:5000]})

print("RANKED_SKILLS",json.dumps(skills,ensure_ascii=False))
print("MISSION_SCREENS",json.dumps(missions[-100:],ensure_ascii=False))
