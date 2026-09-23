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

skills={}
missions=[]
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    if not text:
        continue

    m=re.search(r"Навык:\s*([^⚡]+?)\s*⚡️(.*?)(?:⚠️|Понятно|$)",text)
    if m:
        title=m.group(1).strip()
        effect=m.group(2).strip()
        key=(title,effect)
        skills[key]={"id":r["id"],"title":title,"effect":effect}

    if "Поручения питомцам" in text:
        # Keep only compact windows with rank/cost/reward signals.
        for rank in ["S+"," S "," A "," B "]:
            if rank.strip() in text:
                if re.search(r"отряд:|корм|монет|СОДЕРЖИТ|x\s*\d+",text,re.I):
                    missions.append({"id":r["id"],"text":text[:4200]})
                    break

print("SKILLS",json.dumps(list(skills.values()),ensure_ascii=False))
print("MISSIONS",json.dumps(missions[-120:],ensure_ascii=False))
