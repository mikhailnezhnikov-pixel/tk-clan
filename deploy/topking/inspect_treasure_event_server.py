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
pc=collections.Counter((r["source"],r["path"]) for r in rows)
print("PATH_COUNTS",json.dumps([{"source":k[0],"path":k[1],"count":v} for k,v in pc.most_common()],ensure_ascii=False))

# DOM screen snapshots, compact and unique.
seen=set(); dom=[]
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    if not text: continue
    sig=text[:320]
    if sig in seen: continue
    seen.add(sig)
    dom.append({"id":r["id"],"path":r["path"],"text":text[:1800]})
print("DOM_SNAPSHOTS",json.dumps(dom[:40],ensure_ascii=False))

# Treasure-related assets only.
assets=[]
for r in rows:
    try: vals=json.loads(r.get("assets_json") or "[]")
    except: vals=[]
    for u in vals:
        u=str(u)
        if re.search(r"treasure|minigame/(?:pets|fishing|chests)|event_treasure|golden_berry",u,re.I):
            assets.append(u)
assets=sorted(set(assets))
print("ASSET_COUNT",len(assets))
print("ASSETS",json.dumps(assets[:400],ensure_ascii=False))

# Traverse JSON and surface only compact objects likely defining event config/content.
keywords=re.compile(r"treasure|pet_mission|fishing|minigame_chest|golden_berry|event_treasure|treasurehunt",re.I)
interesting=[]
seen_obj=set()

def short(v,limit=1200):
    try:s=json.dumps(v,ensure_ascii=False,separators=(",",":"))
    except:s=str(v)
    return s if len(s)<=limit else s[:limit]+"…"

def walk(v,path="$",depth=0):
    if depth>12:return
    if isinstance(v,dict):
        # stringify scalar fields only for relevance
        scalar={k:val for k,val in v.items() if isinstance(val,(str,int,float,bool)) or val is None}
        blob=short(scalar,3000)
        keys=" ".join(map(str,v.keys()))
        if keywords.search(keys+" "+blob):
            sig=(path,blob[:500])
            if sig not in seen_obj:
                seen_obj.add(sig)
                interesting.append({"path":path,"keys":list(v.keys())[:40],"value":short(v,2200)})
        for k,val in v.items():
            walk(val,path+"."+str(k),depth+1)
    elif isinstance(v,list):
        for i,val in enumerate(v[:1000]):
            walk(val,path+f"[{i}]",depth+1)

for r in rows:
    pj=r.get("payload_json") or ""
    if not pj: continue
    try: obj=json.loads(pj)
    except: continue
    walk(obj,f"capture[{r['id']}]:{r['path']}")

print("INTERESTING_COUNT",len(interesting))
print("INTERESTING",json.dumps(interesting[:250],ensure_ascii=False))
