import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,page_text,payload_json,captured_at
                                        FROM treasure_guide_captures
                                        ORDER BY id DESC LIMIT 180""")]

# Fresh DOM only: S+ mission cards and short pet-skill popups.
splus=[]
skills=[]
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    if not text:
        continue
    if "Поручения питомцам" in text and "S+" in text:
        splus.append({"id":r["id"],"captured_at":r["captured_at"],"text":text[:4200]})
    if "Питомцы" in text and "Понятно" in text and len(text)<2600:
        if re.search(r"навык|монет|корм|HP|здоров|гоблин|сундук|рыбал|карт|торгов|репутац|ключ",text,re.I):
            skills.append({"id":r["id"],"captured_at":r["captured_at"],"text":text[:2200]})

print("FRESH_SPLUS",json.dumps(splus[:40],ensure_ascii=False))
print("FRESH_SKILLS",json.dumps(skills[:120],ensure_ascii=False))

# Also inspect fresh selective payloads for exact skill lot/config objects.
wanted=re.compile(r"pet_skill|mf_pm_|pet_mission",re.I)
sel=[]
for r in rows:
    p=str(r.get("payload_json") or "")
    if not p or "#treasure-" not in str(r.get("path") or ""):
        continue
    if not wanted.search(p):
        continue
    sel.append({"id":r["id"],"path":r["path"],"captured_at":r["captured_at"],"payload":p[:18000]})
print("FRESH_SELECTIVE",json.dumps(sel[:60],ensure_ascii=False))
