import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,page_text,captured_at
                                        FROM treasure_guide_captures ORDER BY id""")]

skills=[
 "more_money","more_food","fight_hp_up","fight_treasure_goblin",
 "fishing_map_finder","chest_finder","chest_map_finder","map_generator",
 "trader_maps","trader_keys","trader_rep"
]

# A) Exact S+ mission cards/snippets.
splus=[]
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    if not text or "СОДЕРЖИТ" not in text or "S+" not in text: continue
    for m in re.finditer(r"·\s*S\+",text):
        sn=text[max(0,m.start()-180):m.end()+900]
        if re.search(r"корм|монет|шанс|яйц|СОДЕРЖИТ",sn,re.I):
            splus.append({"id":r["id"],"snippet":sn})
print("SPLUS_MISSIONS",json.dumps(splus[:50],ensure_ascii=False))

# B) Skill definition objects from captured API payloads.
def compact(o):
    if not isinstance(o,dict): return o
    out={}
    for k,v in o.items():
        if isinstance(v,(str,int,float,bool)) or v is None:
            out[k]=v
        elif isinstance(v,list) and len(v)<=20:
            try:
                t=json.dumps(v,ensure_ascii=False)
                if len(t)<=8000: out[k]=v
            except: pass
        elif isinstance(v,dict):
            try:
                t=json.dumps(v,ensure_ascii=False)
                if len(t)<=8000: out[k]=v
            except: pass
    return out

found={k:[] for k in skills}
for r in rows:
    p=str(r.get("payload_json") or "")
    if not p: continue
    try: obj=json.loads(p)
    except: continue
    def walk(v,path="$",depth=0):
        if depth>14:return
        if isinstance(v,dict):
            blob=json.dumps(v,ensure_ascii=False,separators=(",",":"))
            for sk in skills:
                if sk in blob and len(found[sk])<25:
                    c=compact(v)
                    if c:
                        found[sk].append({"capture":r["id"],"source":r["path"],"path":path,"obj":c})
            for k,val in v.items():
                if isinstance(val,(dict,list)): walk(val,path+"."+str(k),depth+1)
        elif isinstance(v,list):
            for i,val in enumerate(v[:2500]):
                if isinstance(val,(dict,list)): walk(val,path+f"[{i}]",depth+1)
    walk(obj)
for sk in skills:
    # de-dupe by JSON
    seen=set(); uniq=[]
    for x in found[sk]:
        key=json.dumps(x["obj"],ensure_ascii=False,sort_keys=True)
        if key in seen: continue
        seen.add(key);uniq.append(x)
    print("SKILL_OBJ",sk,json.dumps(uniq[:12],ensure_ascii=False)[:35000])

# C) Visible skill text windows.
for sk,terms in {
 "more_money":["монет","золот"],
 "more_food":["корм","вкусня"],
 "fight_hp_up":["HP","здоров"],
 "fight_treasure_goblin":["гоблин","сокровищ"],
 "fishing_map_finder":["рыбал","карт"],
 "chest_finder":["сундук"],
 "chest_map_finder":["сундук","карт"],
 "map_generator":["карт"],
 "trader_maps":["торгов","карт"],
 "trader_keys":["торгов","ключ"],
 "trader_rep":["торгов","репута"]
}.items():
    hits=[]
    for r in rows:
        text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
        if not text: continue
        if not all(re.search(t,text,re.I) for t in terms): continue
        # prioritize short modal-like text
        if len(text)>12000: continue
        hits.append({"id":r["id"],"text":text[-2400:]})
    print("SKILL_DOM",sk,json.dumps(hits[-20:],ensure_ascii=False))

# D) Localization captures, if any.
loc=[r for r in rows if "localization" in str(r["path"]).lower()]
print("LOCALIZATION_META",json.dumps([{"id":r["id"],"path":r["path"],"len":len(r.get("payload_json") or "")} for r in loc[-30:]],ensure_ascii=False))
