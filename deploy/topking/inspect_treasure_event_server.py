import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,page_text
                                        FROM treasure_guide_captures ORDER BY id""")]

# 1) S+ pet mission economy from visible text.
pet=[]
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    if "Поручения питомцам" not in text and "Питомцы" not in text:
        continue
    if "S+" not in text:
        continue
    for m in re.finditer(r"S\+",text):
        snip=text[max(0,m.start()-500):m.end()+1400]
        if re.search(r"корм|монет|шанс|награ",snip,re.I):
            pet.append({"id":r["id"],"snippet":snip})
print("PET_SPLUS",json.dumps(pet[:30],ensure_ascii=False))

# 2) Relevant non-achievement lot definitions from selective captures.
defs={}
for r in rows:
    if "#treasure-" not in str(r["path"]): continue
    try: obj=json.loads(r["payload_json"] or "{}")
    except: continue
    arr=obj.get("rows",[]) if isinstance(obj,dict) else []
    for item in arr if isinstance(arr,list) else []:
        payload=item.get("payload") if isinstance(item,dict) else None
        if not isinstance(payload,dict): continue
        oid=str(payload.get("id") or "")
        if not oid or "achievement" in oid.lower(): continue
        if not re.search(r"treasury_room_choose|treasurelot_chest|pet_skill|fishing_rod|treasurelot_sword|trader",oid,re.I):
            continue
        defs[oid]={
          "id":oid,
          "cost":payload.get("cost"),
          "lot_view":payload.get("lot_view"),
          "source":r["path"],
          "json_path":item.get("path")
        }
print("PACKET1_LOTS",json.dumps(list(defs.values()),ensure_ascii=False,separators=(",",":")))
