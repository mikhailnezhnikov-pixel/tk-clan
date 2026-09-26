import importlib.util,json,time

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
      SELECT id,path,payload_json,captured_at
      FROM treasure_guide_captures
      WHERE captured_at>=?
      ORDER BY id DESC LIMIT 8000
    """,(int(time.time())-12*3600,))]

states=[]
lot_ids=[]
parsed=[]

def walk_fairs(v,capture,path):
    if isinstance(v,dict):
        fid=str(v.get("id") or v.get("fair_id") or "")
        slots=v.get("fair_slots")
        if fid=="fair_mini_game_trader" and isinstance(slots,list):
            state={"capture":capture,"path":path,"fair_id":fid,"slots":slots}
            states.append(state)
            for slot in slots:
                if isinstance(slot,dict):
                    lid=str(slot.get("shop_lot_id") or slot.get("lot_id") or slot.get("id") or "")
                    if lid and lid not in lot_ids: lot_ids.append(lid)
        for k,x in v.items(): walk_fairs(x,capture,path+"."+str(k))
    elif isinstance(v,list):
        for i,x in enumerate(v): walk_fairs(x,capture,path+f"[{i}]")

for r in rows:
    raw=str(r.get("payload_json") or "")
    if "fair_mini_game_trader" not in raw and "minigame_trader" not in raw:
        continue
    try: obj=json.loads(raw)
    except Exception: continue
    parsed.append((r["id"],obj))
    walk_fairs(obj,r["id"],"$")
    if len(states)>=20: break

definitions={}
targets=set(lot_ids)

def walk_defs(v,capture,path):
    if isinstance(v,dict):
        lid=str(v.get("id") or "")
        if lid in targets and any(k in v for k in ("cost","lot_view","external_cost","limits","priority")):
            definitions.setdefault(lid,{"capture":capture,"path":path,"lot":v})
        for k,x in v.items(): walk_defs(x,capture,path+"."+str(k))
    elif isinstance(v,list):
        for i,x in enumerate(v): walk_defs(x,capture,path+f"[{i}]")

for r in rows:
    raw=str(r.get("payload_json") or "")
    if not any(t in raw for t in targets): continue
    try: obj=json.loads(raw)
    except Exception: continue
    walk_defs(obj,r["id"],"$")
    if len(definitions)>=len(targets): break

print(json.dumps({
  "captured_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
  "states":states[:20],
  "lot_ids":lot_ids,
  "definitions":definitions,
},ensure_ascii=False,indent=2))
