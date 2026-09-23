import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures
                                        WHERE path LIKE '%#treasure-%'
                                        ORDER BY id""")]

print("SELECTIVE_ROWS",len(rows))
for r in rows:
    print("SELECTIVE_META",r["id"],r["path"],len(r["payload_json"] or ""))
    try: obj=json.loads(r["payload_json"] or "{}")
    except Exception as e:
        print("SELECTIVE_PARSE_ERROR",r["id"],repr(e)); continue
    items=obj.get("rows") if isinstance(obj,dict) else None
    if not isinstance(items,list): continue
    for item in items:
        p=str(item.get("path") or "")
        payload=item.get("payload")
        try: text=json.dumps(payload,ensure_ascii=False,separators=(",",":"))
        except: text=str(payload)
        if re.search(r"treasury_room_choose|treasurelot_chest|treasurelot_trader|fairlot_minigame_trader|fair_pet_skill|treasurelot_fishing_rod|treasurelot_sword|shoplot_treasure|golden_berry|treasurehunt_key|treasurehunt_pet|map_fishing|map_fight|map_trader",text,re.I):
            print("SELECTIVE_ITEM",r["id"],p,text[:30000])
