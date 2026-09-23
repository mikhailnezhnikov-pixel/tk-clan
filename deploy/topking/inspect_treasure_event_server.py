import importlib.util, json

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    row=db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures
                      WHERE path='/fair/reroll#treasure-1'
                      ORDER BY id DESC LIMIT 1""").fetchone()

obj=json.loads(row["payload_json"])
arr=obj.get("rows",[])
fairs={}
for item in arr:
    if not isinstance(item,dict): continue
    p=str(item.get("path") or "")
    payload=item.get("payload")
    if not isinstance(payload,dict): continue
    if p.startswith("$.fair[") and p.count(".")==1 and "id" in payload:
        fid=str(payload.get("id") or "")
        fairs[fid]={
          "id":fid,
          "reroll":payload.get("fair_reroll_cost"),
          "slot_count":len(payload.get("fair_slots") or []),
          "slots":[x.get("shop_lot_id") for x in (payload.get("fair_slots") or []) if isinstance(x,dict)][:80]
        }
print("FAIR_COSTS",json.dumps(list(fairs.values()),ensure_ascii=False))
