import importlib.util, json
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE path='/shop/buy' AND payload_json<>''
                                        ORDER BY id""")]

def state(obj):
    fair=None
    for f in obj.get("fair") or []:
        if isinstance(f,dict) and f.get("id")=="fair_mini_game_chests":
            fair=f;break
    if not fair:return None
    slots={int(s.get("id")):(str(s.get("shop_lot_id") or ""),bool(s.get("is_bought")))
           for s in fair.get("fair_slots") or [] if isinstance(s,dict) and s.get("id") is not None}
    inv={}
    for x in obj.get("items") or []:
        if isinstance(x,dict) and x.get("item_id"):
            inv["item:"+str(x["item_id"])]=x.get("quantity")
    for x in obj.get("currencies") or []:
        if isinstance(x,dict) and x.get("currency_id"):
            inv["cur:"+str(x["currency_id"])]=x.get("quantity")
    return slots,inv

parsed=[]
for r in rows:
    try:o=json.loads(r["payload_json"])
    except:continue
    st=state(o)
    if st:parsed.append((r["id"],r["captured_at"],st[0],st[1]))

events=[]
for a,b in zip(parsed,parsed[1:]):
    aid,at,aslots,ainv=a
    bid,bt,bslots,binv=b
    changed=[]
    for sid in sorted(set(aslots)|set(bslots)):
        if aslots.get(sid)!=bslots.get(sid):
            changed.append({"slot":sid,"before":aslots.get(sid),"after":bslots.get(sid)})
    if not changed:continue
    # only transitions where a chest/dig slot became bought or changed lot
    if not any(
        (c["before"] and ("chest_" in c["before"][0] or "digging_spot" in c["before"][0]))
        or (c["after"] and ("chest_" in c["after"][0] or "digging_spot" in c["after"][0]))
        for c in changed
    ): continue
    delta={}
    for k in sorted(set(ainv)|set(binv)):
        av=ainv.get(k);bv=binv.get(k)
        if isinstance(av,(int,float)) and isinstance(bv,(int,float)) and bv!=av:
            delta[k]=bv-av
    events.append({
      "from":aid,"to":bid,"seconds":bt-at,
      "changed":changed,
      "delta":delta
    })
print("CHEST_TRANSITIONS",json.dumps(events,ensure_ascii=False))
