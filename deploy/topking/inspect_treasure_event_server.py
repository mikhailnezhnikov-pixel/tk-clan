import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures
                                        WHERE path LIKE '/shop/view#treasure-%'
                                        ORDER BY id""")]

rx=re.compile(r"(?:trader_0[23]|pet_skill|chest_type|fishing_rod|sword|treasury_room_choose|shoplot_treasure)",re.I)
out=[]
for r in rows:
    try: obj=json.loads(r["payload_json"] or "{}")
    except: continue
    arr=obj.get("rows",[]) if isinstance(obj,dict) else []
    for item in arr if isinstance(arr,list) else []:
        if not isinstance(item,dict): continue
        p=str(item.get("path") or "")
        payload=item.get("payload")
        if not isinstance(payload,dict): continue
        oid=str(payload.get("id") or "")
        if oid and rx.search(oid):
            out.append({
              "capture":r["id"],"source":r["path"],"json_path":p,"id":oid,
              "has_cost":"cost" in payload,"has_lot_view":"lot_view" in payload,
              "object":payload if ("cost" in payload or "lot_view" in payload) else None
            })
print("SHOP_DIRECT_TARGET_ROWS",json.dumps(out,ensure_ascii=False,separators=(",",":")))
