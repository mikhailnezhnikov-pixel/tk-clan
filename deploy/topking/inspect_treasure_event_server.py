import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,page_text,captured_at
                                        FROM treasure_guide_captures ORDER BY id""")]

print("COUNT",len(rows))

# 1) S+ pet mission cards / nearby mission text.
splus=[]
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    if not text:
        continue
    if "Поручения питомцам" in text and ("· S+" in text or " S+ " in text):
        for m in re.finditer(r"S\+",text):
            splus.append({
              "id":r["id"],
              "snippet":text[max(0,m.start()-650):m.end()+1700]
            })
print("SPLUS_MISSIONS",json.dumps(splus[-60:],ensure_ascii=False))

# 2) Short modals/text that may explain pet skills.
skill_words=[
  "монет","корм","здоров","HP","гоблин","сундук","рыбал","карта","торгов",
  "репутац","ключ","навык","питом"
]
mods=[]
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    if not text or len(text)>2600:
        continue
    low=text.lower()
    if any(w.lower() in low for w in skill_words):
        if "Понятно" in text or "ур." in low or "уров" in low:
            mods.append({"id":r["id"],"text":text})
print("SKILL_MODALS",json.dumps(mods[-220:],ensure_ascii=False))

# 3) Treasure-only selective chunks mentioning exact skill ids; keep compact surrounding row.
wanted=[
  "more_money","more_food","fight_hp_up","fight_treasure_goblin",
  "fishing_map_finder","chest_finder","chest_map_finder","map_generator",
  "trader_maps","trader_keys","trader_rep","pet_mission"
]
hits=[]
for r in rows:
    p=str(r.get("payload_json") or "")
    if "#treasure-" not in str(r.get("path") or ""):
        continue
    low=p.lower()
    for term in wanted:
        pos=low.find(term.lower())
        if pos>=0:
            hits.append({
              "id":r["id"],"path":r["path"],"term":term,
              "snippet":p[max(0,pos-1200):pos+5000]
            })
            break
print("SELECTIVE_SKILLS",json.dumps(hits[-180:],ensure_ascii=False))
