import importlib.util, json, re, time
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
      SELECT id,path,payload_json,page_text,captured_at
      FROM treasure_guide_captures
      WHERE payload_json<>'' AND captured_at>=?
      ORDER BY id DESC LIMIT 900
    """,(int(time.time())-72*3600,))]

lots={}
keys=set()
for r in rows:
    raw=str(r.get("payload_json") or "")
    if "mf_fair_pet_skill_" not in raw: continue
    try: obj=json.loads(raw)
    except: continue
    candidates=[]
    if isinstance(obj,dict) and isinstance(obj.get("rows"),list):
        candidates=obj["rows"]
    else:
        candidates=[{"payload":obj,"path":"$"}]
    for item in candidates:
        if not isinstance(item,dict): continue
        p=item.get("payload")
        if not isinstance(p,dict): continue
        pid=str(p.get("id") or "")
        if re.fullmatch(r"mf_fair_pet_skill_.+_r[1-4]",pid):
            if pid not in lots:
                lots[pid]={"capture":r["id"],"capture_path":r["path"],"captured_at":r["captured_at"],"row_path":item.get("path"),"payload":p}
                lv=p.get("lot_view") if isinstance(p.get("lot_view"),dict) else {}
                for k in ("name","desc","contents"):
                    v=lv.get(k)
                    if isinstance(v,str) and v: keys.add(v)

print("LOTS",json.dumps(lots,ensure_ascii=False,separators=(",",":")))

# Search captured localization/API rows for exact name/desc keys from lot definitions.
loc_hits=[]
for r in rows:
    raw=str(r.get("payload_json") or "")
    txt=str(r.get("page_text") or "")
    if not any(k in raw or k in txt for k in keys): continue
    try: obj=json.loads(raw) if raw else None
    except: obj=None
    if isinstance(obj,dict) and isinstance(obj.get("rows"),list):
        for item in obj["rows"]:
            blob=json.dumps(item,ensure_ascii=False,separators=(",",":"))
            matched=[k for k in keys if k in blob]
            if matched:
                loc_hits.append({"capture":r["id"],"path":r["path"],"captured_at":r["captured_at"],"keys":matched,"row":item})
    else:
        # compact windows around each key
        for k in keys:
            pos=raw.find(k)
            if pos>=0:
                loc_hits.append({"capture":r["id"],"path":r["path"],"captured_at":r["captured_at"],"keys":[k],"snippet":raw[max(0,pos-900):pos+5000]})
print("LOCALIZATION",json.dumps(loc_hits[-300:],ensure_ascii=False,separators=(",",":")))

# Latest live skill layouts/rerolls in concise form.
layouts=[]
for r in rows:
    if not r["path"].startswith("/fair/reroll"): continue
    raw=str(r.get("payload_json") or "")
    if "fair_pet_skills" not in raw: continue
    try: obj=json.loads(raw)
    except: continue
    found=[]
    if isinstance(obj,dict) and isinstance(obj.get("rows"),list):
        for item in obj["rows"]:
            p=item.get("payload") if isinstance(item,dict) else None
            if not isinstance(p,dict): continue
            lot=str(p.get("shop_lot_id") or "")
            if re.fullmatch(r"mf_fair_pet_skill_.+_r[1-4]",lot):
                found.append(lot)
    if found:
        layouts.append({"capture":r["id"],"at":r["captured_at"],"path":r["path"],"skills":sorted(set(found))})
print("LAYOUTS",json.dumps(layouts[:80],ensure_ascii=False,separators=(",",":")))
