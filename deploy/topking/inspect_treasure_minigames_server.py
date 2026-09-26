import importlib.util, json, time, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

cutoff=int(time.time())-6*3600
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
      SELECT id,path,payload_json,captured_at
      FROM treasure_guide_captures
      WHERE captured_at>=?
      ORDER BY id DESC LIMIT 5000
    """,(cutoff,))]

keywords=(
    "lights_out","light","lamp","storage","reward",
    "fishing","fish","water","reservoir","rod",
    "enemy","sword","battle","defeated",
    "chest","digging_spot","treasurelot"
)

lots={}
states=[]
strings=[]

def interesting_id(v):
    low=str(v or "").lower()
    return low.startswith("mf_") and any(k in low for k in keywords)

def walk(v,capture,path):
    if isinstance(v,dict):
        lot_id=str(v.get("id") or v.get("shop_lot_id") or "")
        blob=json.dumps(v,ensure_ascii=False).lower()
        if interesting_id(lot_id) and any(k in v for k in ("cost","external_cost","lot_view","content_view","limits","priority")):
            key=lot_id
            if key not in lots:
                lots[key]={"capture":capture,"path":path,"lot":v}
        if "fair_slots" in v and isinstance(v.get("fair_slots"),list):
            slot_rows=v.get("fair_slots") or []
            hits=[]
            for row in slot_rows:
                if not isinstance(row,dict): continue
                rid=str(row.get("shop_lot_id") or row.get("lot_id") or row.get("id") or "")
                if interesting_id(rid):
                    hits.append(row)
            if hits:
                states.append({
                    "capture":capture,
                    "path":path,
                    "fair_id":v.get("id") or v.get("fair_id"),
                    "slots":hits,
                })
        for k,x in v.items():
            walk(x,capture,path+"."+str(k))
    elif isinstance(v,list):
        for i,x in enumerate(v):
            walk(x,capture,path+f"[{i}]")
    elif isinstance(v,str):
        low=v.lower()
        if any(k in low for k in keywords) and len(v)<500:
            if len(strings)<300:
                strings.append({"capture":capture,"path":path,"value":v})

for r in rows:
    raw=str(r.get("payload_json") or "")
    low=raw.lower()
    if not any(k in low for k in keywords):
        continue
    try:
        obj=json.loads(raw)
    except Exception:
        continue
    walk(obj,r["id"],"$")

# Trim states to latest unique signatures.
unique=[]
seen=set()
for st in states:
    sig=(st.get("fair_id"),tuple(sorted(str(x.get("shop_lot_id") or x.get("lot_id") or x.get("id") or "") for x in st["slots"])))
    if sig in seen: continue
    seen.add(sig)
    unique.append(st)
    if len(unique)>=50: break

out={
    "captured_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
    "cutoff":cutoff,
    "lot_count":len(lots),
    "lots":lots,
    "recent_states":unique,
    "strings":strings[:120],
}
print(json.dumps(out,ensure_ascii=False,indent=2))
