import importlib.util,json,time
from collections import defaultdict

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
      SELECT id,capture_key,player_id,path,payload_json,captured_at
      FROM treasure_guide_captures
      WHERE capture_key LIKE 'trace:%'
      ORDER BY id DESC
      LIMIT 1200
    """)]

sessions=defaultdict(list)
for row in rows:
    try:p=json.loads(row.get("payload_json") or "{}")
    except:continue
    if p.get("schema")!="treasure-run-trace-v1":continue
    sid=str(p.get("session_id") or "")
    if sid:sessions[sid].append((row,p))

def flatten(group):
    by={}
    meta={}
    for row,p in sorted(group,key=lambda z:(int(z[1].get("batch") or 0),z[0]["id"])):
        meta.setdefault("started_at",p.get("started_at"))
        meta.setdefault("run_index",p.get("run_index"))
        for e in p.get("events") or []:
            if isinstance(e,dict) and e.get("seq") is not None:
                by[int(e["seq"])]=e
    return [by[k] for k in sorted(by)],meta

allruns=[]
for sid,group in sessions.items():
    events,meta=flatten(group)
    if events:
        allruns.append((str(meta.get("started_at") or ""),sid,events,meta))
allruns.sort(reverse=True)

print("LATEST_AUTOMAP_TRANSITION_TRACE")
for started,sid,events,meta in allruns[:1]:
    print(json.dumps({"session_id":sid,"started_at":started,"run_index":meta.get("run_index"),"events":len(events)},ensure_ascii=False))
    prev_screen=None
    for e in events:
        typ=str(e.get("type") or "")
        d=e.get("data") if isinstance(e.get("data"),dict) else {}
        sc=str(e.get("screen") or "")
        if sc!=prev_screen:
            print(json.dumps({"seq":e.get("seq"),"at":e.get("at"),"type":"screen-change","from":prev_screen,"to":sc},ensure_ascii=False))
            prev_screen=sc
        if typ=="click":
            t=d.get("target") if isinstance(d.get("target"),dict) else {}
            txt=str(t.get("text") or "").replace("\n"," ")[:220]
            lot=str(t.get("lotId") or "")
            if txt or lot:
                print(json.dumps({
                    "seq":e.get("seq"),"at":e.get("at"),"screen":sc,"type":"click",
                    "text":txt,"lot":lot,"clickId":d.get("clickId")
                },ensure_ascii=False))
        elif typ=="network":
            path=str(d.get("path") or "")
            if path in ("/fair/reroll","/shop/buy"):
                req=d.get("request") if isinstance(d.get("request"),dict) else {}
                resp=d.get("response") if isinstance(d.get("response"),dict) else {}
                print(json.dumps({
                    "seq":e.get("seq"),"at":e.get("at"),"screen":sc,"type":"network",
                    "path":path,"status":d.get("status"),"fair_id":req.get("fair_id"),
                    "shop_lot_id":req.get("shop_lot_id"),"slot_id":req.get("slot_id"),
                    "message":resp.get("message")
                },ensure_ascii=False))
        elif typ=="blocked-action":
            print(json.dumps({
                "seq":e.get("seq"),"at":e.get("at"),"screen":sc,"type":"blocked",
                "reason":d.get("reason"),"status":d.get("status"),"path":d.get("path")
            },ensure_ascii=False))
    print("END_LATEST_TRANSITION_SESSION")
