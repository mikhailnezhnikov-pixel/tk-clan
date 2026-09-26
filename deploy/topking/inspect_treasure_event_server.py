import importlib.util, json, time
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

targets={
 "mf_treasurelot_chest_digging_spot_sl4",
 "mf_treasurelot_chest_digging_spot_sl5",
 "mf_treasurelot_chest_digging_spot_sl6",
 "mf_treasurelot_chest_digging_spot_sl7",
 "mf_treasurelot_chest_digging_spot_sl8",
 "mf_treasurelot_chest_digging_spot_sl9",
 "mf_treasurelot_chest_type_015",
 "mf_treasurelot_chest_type_01",
 "mf_treasurelot_chest_type_02",
 "mf_treasurelot_chest_type_03",
}
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
      SELECT id,path,payload_json,captured_at
      FROM treasure_guide_captures
      WHERE captured_at>=?
      ORDER BY id DESC LIMIT 600
    """,(int(time.time())-24*3600,))]

seen={}
def walk(v,capture,path):
    if isinstance(v,dict):
        lot_id=str(v.get("id") or "")
        if lot_id in targets and any(k in v for k in ("cost","external_cost","lot_view","limits")):
            seen.setdefault(lot_id,{"capture":capture,"path":path,"lot":v})
        for k,x in v.items(): walk(x,capture,path+"."+str(k))
    elif isinstance(v,list):
        for i,x in enumerate(v): walk(x,capture,path+f"[{i}]")

for r in rows:
    raw=str(r.get("payload_json") or "")
    if not any(t in raw for t in targets): continue
    try: obj=json.loads(raw)
    except: continue
    walk(obj,r["id"],"$")
    if len(seen)>=len(targets): break

print(json.dumps(seen,ensure_ascii=False,indent=2))
