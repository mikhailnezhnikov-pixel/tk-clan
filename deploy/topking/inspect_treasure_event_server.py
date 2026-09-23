import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

targets=[
 "mf_fair_treasury_room_choose_way_1",
 "mf_fair_treasury_room_choose_way_2",
 "mf_fair_treasury_room_choose_way_3",
 "mf_treasurelot_chest_type_015",
 "mf_treasurelot_chest_type_02",
 "mf_treasurelot_chest_type_03",
 "treasure_search_result",
 "fair_treasury_room",
 "fair_mini_game_chests"
]

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,page_text,captured_at
                                        FROM treasure_guide_captures ORDER BY id""")]

def smallest(v,term,path="$",depth=0,best=None):
    if depth>20:return best
    try: blob=json.dumps(v,ensure_ascii=False,separators=(",",":"))
    except:return best
    if term.lower() not in blob.lower():return best
    if best is None or len(blob)<best[0]:best=(len(blob),path,v)
    if isinstance(v,dict):
        for k,val in v.items():
            if isinstance(val,(dict,list)):best=smallest(val,term,path+"."+str(k),depth+1,best)
    elif isinstance(v,list):
        for i,val in enumerate(v[:6000]):
            if isinstance(val,(dict,list)):best=smallest(val,term,path+f"[{i}]",depth+1,best)
    return best

for term in targets:
    hits=[]
    for r in rows:
        raw=str(r.get("payload_json") or "")
        if term.lower() not in raw.lower():continue
        try: obj=json.loads(raw)
        except:
            pos=raw.lower().find(term.lower())
            hits.append({"capture":r["id"],"capture_path":r["path"],"snippet":raw[max(0,pos-1600):pos+6500]})
            continue
        b=smallest(obj,term)
        if b:
            size,path,val=b
            hits.append({"capture":r["id"],"capture_path":r["path"],"json_path":path,"size":size,"value":val})
    print("TARGET",term,json.dumps(hits[-20:],ensure_ascii=False)[:60000])

# Exact visible cards / screens for treasury + chest hunt.
screens=[]
seen=set()
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    if not text:continue
    if not re.search(r"Сокровищниц|Охота за сундуками|сундук|Путь 1|Путь 2|Путь 3|Раскоп",text,re.I):continue
    if not ("СОДЕРЖИТ" in text or "МОЖЕТ СОДЕРЖАТЬ" in text or "Понятно" in text or "Сокровищница" in text or "Охота за сундуками" in text):
        continue
    key=text[:1800]
    if key in seen:continue
    seen.add(key)
    screens.append({"id":r["id"],"captured_at":r["captured_at"],"text":text[:6500]})
print("SCREENS",json.dumps(screens[-160:],ensure_ascii=False))
