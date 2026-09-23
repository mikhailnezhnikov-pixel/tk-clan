import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    row=db.execute("SELECT id,payload_json FROM treasure_guide_captures WHERE path LIKE '/fair/reroll#treasure-%' ORDER BY id DESC LIMIT 1").fetchone()
obj=json.loads(row["payload_json"])
out=[]
for x in obj.get("rows",[]):
    if not isinstance(x,dict): continue
    p=x.get("payload")
    if not isinstance(p,dict): continue
    pid=str(p.get("id") or "")
    if pid.startswith("minigame_pet_skill_") or pid in ("minigame_pet_max_skill_level","minigame_pet_skills_count","minigame_pet_current_slots"):
        out.append({"path":x.get("path"),"id":pid,"quantity":p.get("quantity")})
print("SKILL_COUNTERS",json.dumps(out,ensure_ascii=False))
