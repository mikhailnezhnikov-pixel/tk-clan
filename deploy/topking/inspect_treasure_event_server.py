import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE path LIKE '/shop/view#treasure-%'
                                        ORDER BY id DESC LIMIT 40""")]

found=[]
rx=re.compile(r"^(?:mf_fairlot_minigame_trader_(?:01|02|03)_.+|mf_treasurelot_trader_type_(?:01|02|03)_active_rep_5)$")
for r in rows:
    try: obj=json.loads(r["payload_json"])
    except: continue
    for x in obj.get("rows",[]) if isinstance(obj,dict) else []:
        if not isinstance(x,dict): continue
        p=x.get("payload")
        if not isinstance(p,dict): continue
        pid=str(p.get("id") or "")
        if rx.match(pid):
            found.append({"capture":r["id"],"captured_at":r["captured_at"],"payload":p})
print("TRADER_PRIORITY_COUNT",len(found))
print("TRADER_PRIORITY_META",json.dumps([
  {"capture":x["capture"],"captured_at":x["captured_at"],"id":x["payload"].get("id")}
  for x in found
],ensure_ascii=False))
