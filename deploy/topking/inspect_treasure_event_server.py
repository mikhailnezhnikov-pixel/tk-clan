import importlib.util, json, re, collections

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,source,path,payload_json,page_text,assets_json,captured_at
                                        FROM treasure_guide_captures
                                        ORDER BY id""")]

relevant_fairs={
  "fair_treasures","fair_mini_game_fishing","fair_mini_game_trader",
  "fair_mini_game_chests","fair_mini_game_fight","fair_lights_out",
  "fair_treasury_room","fair_minigame_collection","fair_pet_gallery",
  "fair_pet_skills","fair_pet_missions","fair_pet_companions"
}

latest=None
for r in rows:
    if r["path"] not in ("/shop/buy","/fair/reroll") or not r["payload_json"]:
        continue
    try: obj=json.loads(r["payload_json"])
    except: continue
    fairs=obj.get("fair")
    if isinstance(fairs,list):
        latest=(r["id"],fairs)
if latest:
    rid,fairs=latest
    out=[]
    for fair in fairs:
        if not isinstance(fair,dict): continue
        fid=str(fair.get("id") or "")
        slots=fair.get("fair_slots")
        slot_ids=[]
        if isinstance(slots,list):
            for slot in slots:
                if not isinstance(slot,dict): continue
                lot=str(slot.get("shop_lot_id") or "")
                if "treasure" in lot or "minigame" in lot or fid in relevant_fairs:
                    slot_ids.append({"slot":slot.get("id"),"lot":lot,"bought":slot.get("is_bought")})
        if fid in relevant_fairs or slot_ids:
            cost=fair.get("fair_reroll_cost")
            out.append({"id":fid,"cost":cost,"slots":slot_ids[:160],"slot_count":len(slots) if isinstance(slots,list) else 0})
    print("FAIR_STATE_CAPTURE",rid)
    print("FAIR_STATE",json.dumps(out,ensure_ascii=False)[:70000])

# Extract achievement modal snapshots exactly (title + rewards + condition).
mods=[]
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    if "Достижения" not in text or "СОДЕРЖИТ" not in text or "Понятно" not in text:
        continue
    marker="Обновить HK "
    if marker in text:
        modal=text.split(marker,1)[1]
    else:
        pos=text.rfind(" HK ")
        modal=text[pos+4:] if pos>=0 else text
    if "СОДЕРЖИТ" in modal:
        mods.append({"id":r["id"],"modal":modal[:1800]})
print("ACHIEVEMENT_MODALS",json.dumps(mods,ensure_ascii=False))

# Extract pet modal snapshots.
petmods=[]
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    if "Питомцы" not in text or "Понятно" not in text:
        continue
    pos=text.rfind(" HK ")
    modal=text[pos+4:] if pos>=0 else text
    if len(modal)<2500:
        petmods.append({"id":r["id"],"modal":modal})
print("PET_MODALS",json.dumps(petmods,ensure_ascii=False))

# Extract treasure-only selective chunks if already arriving.
selective=[]
for r in rows:
    if "#treasure-" in str(r["path"]):
        selective.append({"id":r["id"],"path":r["path"],"len":len(r["payload_json"] or "")})
print("SELECTIVE",json.dumps(selective,ensure_ascii=False))
