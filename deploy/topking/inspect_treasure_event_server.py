import importlib.util, json

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

terms=[
 "more_money","more_food","fight_hp_up","fight_treasure_goblin",
 "fishing_map_finder","chest_finder","chest_map_finder","map_generator",
 "trader_maps","trader_keys","trader_rep"
]

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json
                                        FROM treasure_guide_captures
                                        WHERE payload_json<>'' ORDER BY id""")]

def find_smallest(v,term,path="$",best=None,depth=0):
    if depth>18:
        return best
    try:
        blob=json.dumps(v,ensure_ascii=False,separators=(",",":"))
    except:
        return best
    if term.lower() not in blob.lower():
        return best
    size=len(blob)
    if best is None or size<best[0]:
        best=(size,path,v)
    if isinstance(v,dict):
        for k,val in v.items():
            best=find_smallest(val,term,path+"."+str(k),best,depth+1)
    elif isinstance(v,list):
        for i,val in enumerate(v[:4000]):
            best=find_smallest(val,term,path+f"[{i}]",best,depth+1)
    return best

for term in terms:
    hits=[]
    for r in rows:
        try:
            obj=json.loads(r["payload_json"])
        except:
            continue
        best=find_smallest(obj,term)
        if best:
            size,path,val=best
            hits.append({
              "capture":r["id"],"capture_path":r["path"],
              "json_path":path,"size":size,"value":val
            })
    print("TERMOBJ",term,json.dumps(hits[-12:],ensure_ascii=False)[:50000])
