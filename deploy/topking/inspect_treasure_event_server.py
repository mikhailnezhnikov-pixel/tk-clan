import importlib.util, json, time, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
      SELECT id,path,payload_json,captured_at
      FROM treasure_guide_captures
      WHERE captured_at>=? AND path='/shop/buy'
      ORDER BY id DESC LIMIT 120
    """,(int(time.time())-12*3600,))]

def find_chest_fair(obj):
    candidates=[]
    def walk(v):
        if isinstance(v,dict):
            if v.get("id")=="fair_mini_game_chests" and isinstance(v.get("fair_slots"),list):
                candidates.append(v)
            for x in v.values(): walk(x)
        elif isinstance(v,list):
            for x in v: walk(x)
    walk(obj)
    return candidates[-1] if candidates else None

def collect_items(obj):
    out=[]
    def walk(v):
        if isinstance(v,dict):
            iid=v.get("item_id")
            if isinstance(iid,str) and any(k in iid.lower() for k in ("treasure","berry","key","chest","map")):
                out.append((iid,v.get("quantity")))
            for x in v.values(): walk(x)
        elif isinstance(v,list):
            for x in v: walk(x)
    walk(obj)
    return out

for r in rows:
    try: obj=json.loads(r.get("payload_json") or "")
    except: continue
    fair=find_chest_fair(obj)
    if not fair: continue
    slots=sorted([
      {"id":x.get("id"),"is_bought":x.get("is_bought"),"lot":x.get("shop_lot_id")}
      for x in fair.get("fair_slots",[]) if isinstance(x,dict)
    ], key=lambda x:(x["id"] or 0))
    interesting=any(
      (x.get("lot") or "").startswith("mf_treasurelot_bought_")
      or x.get("is_bought")
      or "empty_spot" in (x.get("lot") or "")
      for x in slots
    )
    if not interesting: continue
    print("STATE",r["id"],r["captured_at"],json.dumps(slots,ensure_ascii=False,separators=(",",":")))
    items=collect_items(obj)
    if items:
        dedup={}
        for k,v in items: dedup[k]=v
        print("ITEMS",r["id"],json.dumps(dedup,ensure_ascii=False,separators=(",",":")))
