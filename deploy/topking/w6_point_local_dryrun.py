#!/usr/bin/env python3
import json, sys, time, urllib.parse, urllib.request

src=json.load(open(sys.argv[1],encoding="utf-8"))
out_path=sys.argv[2]
key=src["map_key"]

def decode(flat):
    lng=lat=0
    out=[]
    for i in range(0,len(flat),3):
        lng+=int(flat[i]); lat+=int(flat[i+1]); flag=int(flat[i+2])
        inv=flag>=7
        rooms=flag-8 if inv else flag
        out.append({"point_index":i//3,"lon":lng/1e5,"lat":lat/1e5,
                    "room_count":rooms,"investment":inv,"source_flag":flag})
    return out

def inside(ring,x,y):
    if len(ring)<3: return False
    ok=False; j=len(ring)-1
    for i in range(len(ring)):
        xi,yi=ring[i]; xj,yj=ring[j]
        if (yi>y)!=(yj>y):
            z=(xj-xi)*(y-yi)/(yj-yi)+xi
            if x<z: ok=not ok
        j=i
    return ok

def polygons(e):
    if e.get("type")=="way":
        g=[(float(n["lon"]),float(n["lat"])) for n in (e.get("geometry") or [])
           if "lon" in n and "lat" in n]
        return [g] if len(g)>=3 else []
    segs=[]
    for m in e.get("members") or []:
        if m.get("role")!="outer": continue
        g=[(float(n["lon"]),float(n["lat"])) for n in (m.get("geometry") or [])
           if "lon" in n and "lat" in n]
        if len(g)>=2: segs.append(g)
    rings=[]
    while segs:
        ring=segs.pop(0)
        changed=True
        while changed and segs:
            changed=False
            for i,g in enumerate(segs):
                if ring[-1]==g[0]:
                    ring.extend(g[1:]); segs.pop(i); changed=True; break
                if ring[-1]==g[-1]:
                    ring.extend(list(reversed(g[:-1]))); segs.pop(i); changed=True; break
                if ring[0]==g[-1]:
                    ring=g[:-1]+ring; segs.pop(i); changed=True; break
                if ring[0]==g[0]:
                    ring=list(reversed(g[1:]))+ring; segs.pop(i); changed=True; break
        if len(ring)>=3: rings.append(ring)
    return rings

ENDPOINTS=(
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)

def call(q):
    body=urllib.parse.urlencode({"data":q}).encode()
    last=None
    for round_no in range(2):
        for endpoint in ENDPOINTS:
            try:
                req=urllib.request.Request(endpoint,data=body,headers={"User-Agent":"TopKing-W6/5.0"})
                with urllib.request.urlopen(req,timeout=28) as r:
                    return json.load(r)
            except Exception as e:
                last=repr(e)
        time.sleep(2+round_no*2)
    raise RuntimeError(str(last))

def add_elements(store,data):
    for e in data.get("elements",[]):
        typ=e.get("type"); eid=e.get("id")
        if typ not in ("way","relation") or eid is None: continue
        ps=polygons(e)
        if ps:
            store[("way" if typ=="way" else "relation")+str(eid)]=ps

query_failures=[]
features={}

def fetch_batch(batch):
    if not batch: return
    clauses=[]
    for p in batch:
        clauses.append(f'way(around:20,{p["lat"]},{p["lon"]})["building"];')
        clauses.append(f'relation(around:20,{p["lat"]},{p["lon"]})["building"];')
    q='[out:json][timeout:25];('+''.join(clauses)+');out geom;'
    try:
        add_elements(features,call(q))
        return
    except Exception as e:
        if len(batch)>1:
            mid=len(batch)//2
            fetch_batch(batch[:mid])
            fetch_batch(batch[mid:])
            return
        p=batch[0]
        query_failures.append({"point_index":p["point_index"],"error":repr(e)})

pts=decode(src.get("points") or [])
for start in range(0,len(pts),10):
    fetch_batch(pts[start:start+10])

can={x["building_id"]:x for x in src.get("canonical_buildings") or []}
unique=[]; unmatched=[]; ambiguous=[]; used={}
failed_indices={x["point_index"] for x in query_failures}

for p in pts:
    if p["point_index"] in failed_indices:
        unmatched.append({**p,"reason":"osm_query_failed"})
        continue
    hits=[bid for bid,ps in features.items()
          if any(inside(poly,p["lon"],p["lat"]) for poly in ps)]
    if not hits:
        unmatched.append({**p,"reason":"no_exact_osm_building_containment"})
        continue
    if len(hits)>1:
        ambiguous.append({**p,"candidates":sorted(hits),"reason":"multiple_buildings"})
        continue
    bid=hits[0]
    if bid in used:
        ambiguous.append({**p,"candidates":[bid],"reason":"duplicate_building_point",
                          "other_point_index":used[bid]})
        continue
    used[bid]=p["point_index"]
    cur=can.get(bid)
    row={**p,"building_id":bid,"existing":bool(cur)}
    if cur:
        row.update({
            "canonical_room_count":cur["room_count"],
            "canonical_source":cur["knowledge_source"],
            "canonical_observed_at":cur["knowledge_observed_at"],
            "canonical_is_invest":cur["is_invest"],
        })
    unique.append(row)

result={
    "map_key":key,
    "canonical_area_id":src["canonical_area_id"],
    "point_count":len(pts),
    "points":unique,
    "unmatched":unmatched,
    "ambiguous":ambiguous,
    "osm_query_failures":query_failures,
}
open(out_path,"w",encoding="utf-8").write(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True))
print(json.dumps({
    "map_key":key,"points":len(pts),"unique":len(unique),
    "unmatched":len(unmatched),"ambiguous":len(ambiguous),
    "query_failures":len(query_failures)
},sort_keys=True))
