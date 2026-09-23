import importlib.util, json
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

watch_items={
 "item_treasurehunt_energy","item_treasurehunt_cur_coins",
 "item_treasurehunt_key_common","item_treasurehunt_key_uncommon","item_treasurehunt_key_epic",
 "item_event_treasure_map_path","item_event_treasure_map_trader","item_event_treasure_map_fishing","item_event_treasure_map_fight",
 "item_event_treasure_golden_berry",
 "item_pet_mothcat_egg_01","item_pet_mothcat_egg_02","item_pet_mothcat_egg_03",
 "item_pet_fish_egg_01","item_pet_fish_egg_02","item_pet_fish_egg_03"
}
watch_cur={"cur_gold","cur_cap"}

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,captured_at FROM treasure_guide_captures
                                        WHERE path='/shop/buy' AND payload_json<>''
                                        ORDER BY id""")]

def inv(obj):
    out={}
    for x in obj.get("items") or []:
        if isinstance(x,dict) and x.get("item_id") in watch_items:
            out[x["item_id"]]=x.get("quantity")
    for x in obj.get("currencies") or []:
        if isinstance(x,dict) and x.get("currency_id") in watch_cur:
            out[x["currency_id"]]=x.get("quantity")
    return out

def fair_summary(obj):
    out={}
    for fair in obj.get("fair") or []:
        if not isinstance(fair,dict):continue
        fid=str(fair.get("id") or "")
        if fid not in ("fair_mini_game_chests","fair_treasury_room"):continue
        slots=[]
        for s in fair.get("fair_slots") or []:
            if isinstance(s,dict):
                lot=str(s.get("shop_lot_id") or "")
                if fid=="fair_treasury_room":
                    if s.get("id") in (1,2,3) or lot!="mf_fairlot_empty":
                        slots.append([s.get("id"),lot,bool(s.get("is_bought"))])
                else:
                    slots.append([s.get("id"),lot,bool(s.get("is_bought"))])
        out[fid]=slots
    return out

records=[]
for r in rows:
    try:obj=json.loads(r["payload_json"])
    except:continue
    fs=fair_summary(obj)
    if not fs:continue
    records.append({"id":r["id"],"captured_at":r["captured_at"],"fair":fs,"inv":inv(obj)})

print("TRANS",json.dumps(records,ensure_ascii=False))
