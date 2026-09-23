import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,page_text FROM treasure_guide_captures ORDER BY id""")]

# Short modal tails from the Pets section. These are the best source for localized skill/effect text.
mods=[]
seen=set()
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    if "Питомцы" not in text or "Понятно" not in text or len(text)>7000: continue
    pos=text.rfind(" HK ")
    tail=text[pos+4:] if pos>=0 else text
    if "Понятно" not in tail: continue
    key=tail[-1800:]
    if key in seen: continue
    seen.add(key)
    mods.append({"id":r["id"],"text":key})
print("PET_MODAL_TAILS",json.dumps(mods[-80:],ensure_ascii=False))

# Exact shop lot objects for pet skills and pet missions from selective /shop/view captures.
out={}
for r in rows:
    if "#treasure-" not in str(r["path"]): continue
    try: obj=json.loads(r["payload_json"] or "{}")
    except: continue
    for item in obj.get("rows",[]) if isinstance(obj,dict) else []:
        p=item.get("payload") if isinstance(item,dict) else None
        if not isinstance(p,dict): continue
        oid=str(p.get("id") or "")
        if not re.search(r"pet_skill|pet_mission|pet_.*mission|mission_.*pet",oid,re.I): continue
        if oid not in out:
            out[oid]={"id":oid,"cost":p.get("cost"),"lot_view":p.get("lot_view"),"path":item.get("path"),"source":r["path"]}
print("PET_LOTS",json.dumps(list(out.values()),ensure_ascii=False,separators=(",",":")))

# Active mission fair state and lot ids.
mission_states=[]
for r in rows:
    if r["path"] not in ("/fair/reroll","/shop/buy"): continue
    try: obj=json.loads(r["payload_json"] or "{}")
    except: continue
    fairs=obj.get("fair")
    if not isinstance(fairs,list): continue
    for fair in fairs:
        if isinstance(fair,dict) and fair.get("id")=="fair_pet_missions":
            mission_states.append({"capture":r["id"],"state":fair})
print("PET_MISSION_FAIR",json.dumps(mission_states[-8:],ensure_ascii=False)[:50000])
