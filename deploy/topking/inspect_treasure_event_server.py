import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE payload_json<>''
                                        ORDER BY id""")]

# 1) Collect all trader lot ids actually observed in fair states.
observed=set()
for r in rows:
    if r["path"] not in ("/shop/buy","/fair/reroll"):
        continue
    try:obj=json.loads(r["payload_json"])
    except:continue
    fairs=obj.get("fair") if isinstance(obj,dict) else None
    if not isinstance(fairs,list):continue
    for fair in fairs:
        if not isinstance(fair,dict) or fair.get("id")!="fair_mini_game_trader":continue
        for s in fair.get("fair_slots") or []:
            if not isinstance(s,dict):continue
            lot=str(s.get("shop_lot_id") or "")
            if lot and lot not in ("mf_fairlot_empty","mf_fair_pet_skill_locked_by_bonus"):
                observed.add(lot)
print("OBSERVED_IDS",json.dumps(sorted(observed),ensure_ascii=False))

# 2) Resolve exact full objects from fresh prioritized/selective /shop/view rows first.
resolved={}
for r in rows:
    if not str(r["path"]).startswith("/shop/view#treasure-"):
        continue
    try:obj=json.loads(r["payload_json"])
    except:continue
    for x in obj.get("rows",[]) if isinstance(obj,dict) else []:
        if not isinstance(x,dict):continue
        p=x.get("payload")
        if not isinstance(p,dict):continue
        pid=str(p.get("id") or "")
        if pid in observed and ("cost" in p or "lot_view" in p):
            resolved[pid]=p

# 3) For unresolved ids, search valid JSON captures recursively for smallest complete object.
def walk(v,target,path="$",depth=0,best=None):
    if depth>18:return best
    if isinstance(v,dict):
        if str(v.get("id") or "")==target and ("cost" in v or "lot_view" in v):
            blob=json.dumps(v,ensure_ascii=False,separators=(",",":"))
            if best is None or len(blob)<best[0]:best=(len(blob),path,v)
        for k,val in v.items():
            if isinstance(val,(dict,list)):best=walk(val,target,path+"."+str(k),depth+1,best)
    elif isinstance(v,list):
        for i,val in enumerate(v[:8000]):
            if isinstance(val,(dict,list)):best=walk(val,target,path+f"[{i}]",depth+1,best)
    return best

for target in sorted(observed):
    if target in resolved:continue
    for r in rows:
        raw=str(r["payload_json"] or "")
        if target not in raw:continue
        try:obj=json.loads(raw)
        except:continue
        b=walk(obj,target)
        if b:
            resolved[target]=b[2]
            break

out=[]
for oid in sorted(observed):
    p=resolved.get(oid)
    if not p:
        out.append({"id":oid,"missing":True});continue
    lv=p.get("lot_view") or {}
    out.append({
      "id":oid,
      "cost":p.get("cost"),
      "content":lv.get("content_view"),
      "contents":lv.get("contents"),
      "name":lv.get("name"),
      "desc":lv.get("desc"),
      "icon":lv.get("icon_card")
    })
print("TRADER_EXACT",json.dumps(out,ensure_ascii=False))

# 4) Current and historical trader states, grouped by sets to identify type I/II/III.
states=[]
seen=set()
for r in rows:
    if r["path"] not in ("/shop/buy","/fair/reroll"):continue
    try:obj=json.loads(r["payload_json"])
    except:continue
    fairs=obj.get("fair") if isinstance(obj,dict) else None
    if not isinstance(fairs,list):continue
    for fair in fairs:
        if not isinstance(fair,dict) or fair.get("id")!="fair_mini_game_trader":continue
        lots=tuple(sorted(str(s.get("shop_lot_id") or "") for s in (fair.get("fair_slots") or []) if isinstance(s,dict) and s.get("shop_lot_id") not in (None,"","mf_fairlot_empty","mf_fair_pet_skill_locked_by_bonus")))
        if lots in seen:continue
        seen.add(lots)
        states.append({"capture":r["id"],"lots":lots})
print("TRADER_SETS",json.dumps(states,ensure_ascii=False))
