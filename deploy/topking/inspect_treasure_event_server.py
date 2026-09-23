from pathlib import Path
import importlib.util, json, re, collections

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,source,path,payload_json,page_text,assets_json,captured_at
                                        FROM treasure_guide_captures
                                        ORDER BY captured_at,id""")]

print("COUNT",len(rows))
for target in ["/quests","/client_config","/shop/view","/battlepass/claim"]:
    subset=[r for r in rows if r["source"]=="api" and r["path"]==target]
    print("TARGET",target,"ROWS",len(subset))
    for r in subset[-3:]:
        try: obj=json.loads(r["payload_json"])
        except Exception as e:
            print("PARSE_ERROR",target,repr(e)); continue
        def outline(v,depth=0):
            if depth>2:return type(v).__name__
            if isinstance(v,dict):
                return {k:outline(val,depth+1) for k,val in list(v.items())[:80]}
            if isinstance(v,list):
                return {"list_len":len(v),"sample":[outline(x,depth+1) for x in v[:3]]}
            return type(v).__name__
        print("OUTLINE",target,json.dumps(outline(obj),ensure_ascii=False)[:12000])
        # print compact matching objects from this payload
        pats=re.compile(r"treasure|minigame|quest|pet_mission|golden_berry|map_",re.I)
        found=[]
        def walk(v,path="$",depth=0):
            if depth>12 or len(found)>=180:return
            if isinstance(v,dict):
                scalar={k:val for k,val in v.items() if isinstance(val,(str,int,float,bool)) or val is None}
                blob=json.dumps(scalar,ensure_ascii=False)
                if pats.search(blob) or pats.search(" ".join(map(str,v.keys()))):
                    # keep only reasonably compact dicts / selected fields
                    selected={}
                    for k,val in v.items():
                        if isinstance(val,(str,int,float,bool)) or val is None:
                            selected[k]=val
                        elif isinstance(val,list) and len(val)<=12 and all(isinstance(x,(str,int,float,bool,dict)) for x in val):
                            selected[k]=val
                        elif isinstance(val,dict) and len(val)<=12:
                            selected[k]=val
                    found.append({"path":path,"data":selected})
                for k,val in v.items(): walk(val,path+"."+str(k),depth+1)
            elif isinstance(v,list):
                for i,val in enumerate(v[:1000]): walk(val,path+f"[{i}]",depth+1)
        walk(obj)
        print("MATCHES",target,json.dumps(found,ensure_ascii=False)[:36000])

# Print DOM snapshots with the sections we care about, not all.
for section in ["Достижения","Задания","Магазин","Питомцы","Поручения питомцам","Линейки наград","Карта Сокровищ"]:
    best=[]
    for r in rows:
        t=str(r.get("page_text") or "")
        if section not in t: continue
        # prefer snapshot where section appears as active title more than once / meaningful body
        score=len(t)
        best.append((score,r["id"],re.sub(r"\s+"," ",t).strip()[:8000]))
    best=sorted(best,reverse=True)[:3]
    print("DOM_SECTION",section,json.dumps([{"id":i,"text":t} for _,i,t in best],ensure_ascii=False))
