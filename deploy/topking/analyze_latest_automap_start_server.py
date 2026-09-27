import importlib.util,json
from collections import defaultdict

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
      SELECT id,capture_key,payload_json,captured_at
      FROM treasure_guide_captures
      WHERE capture_key LIKE 'trace:%'
      ORDER BY id DESC
      LIMIT 5000
    """)]

sessions=defaultdict(list)
for row in rows:
    try:p=json.loads(row.get("payload_json") or "{}")
    except:continue
    if p.get("schema")!="treasure-run-trace-v1":continue
    sid=str(p.get("session_id") or "")
    if sid:sessions[sid].append((row,p))

runs=[]
for sid,group in sessions.items():
    events={}
    started=""
    for row,p in sorted(group,key=lambda z:(int(z[1].get("batch") or 0),z[0]["id"])):
        started=started or str(p.get("started_at") or "")
        for e in p.get("events") or []:
            if isinstance(e,dict) and e.get("seq") is not None:
                events[int(e["seq"])]=e
    ev=[events[k] for k in sorted(events)]
    if any(str(e.get("screen") or "")=="fishing" for e in ev):
        runs.append((started,sid,ev))
runs.sort(reverse=True)

print("LATEST_FISHING_ZERO_BALANCE_TRACE")
for started,sid,ev in runs[:6]:
    print(json.dumps({"session_id":sid,"started_at":started,"events":len(ev)},ensure_ascii=False))
    prev=None
    for e in ev:
        screen=str(e.get("screen") or "")
        typ=str(e.get("type") or "")
        d=e.get("data") if isinstance(e.get("data"),dict) else {}
        interesting = screen=="fishing" or prev=="fishing"
        if screen!=prev and ("fishing" in (screen,prev)):
            print(json.dumps({"seq":e.get("seq"),"at":e.get("at"),"type":"screen-change","from":prev,"to":screen},ensure_ascii=False))
        if interesting:
            if typ=="click":
                t=d.get("target") if isinstance(d.get("target"),dict) else {}
                print(json.dumps({
                    "seq":e.get("seq"),"at":e.get("at"),"screen":screen,"type":"click",
                    "text":str(t.get("text") or "").replace("\n"," ")[:220],
                    "lotId":t.get("lotId"),"pointerType":d.get("pointerType")
                },ensure_ascii=False))
            elif typ=="network":
                req=d.get("request") if isinstance(d.get("request"),dict) else {}
                resp=d.get("response") if isinstance(d.get("response"),dict) else {}
                print(json.dumps({
                    "seq":e.get("seq"),"at":e.get("at"),"screen":screen,"type":"network",
                    "path":d.get("path"),"status":d.get("status"),
                    "fair_id":req.get("fair_id"),"shop_lot_id":req.get("shop_lot_id"),
                    "slot_id":req.get("slot_id"),"message":resp.get("message"),
                    "response":resp
                },ensure_ascii=False)[:5000])
            elif typ=="snapshot":
                lots=d.get("lots") if isinstance(d.get("lots"),list) else []
                print(json.dumps({
                    "seq":e.get("seq"),"at":e.get("at"),"screen":screen,"type":"snapshot",
                    "lots":[x for x in lots if isinstance(x,dict) and ('fishing' in str(x.get("lotId") or "") or 'rod' in str(x.get("lotId") or ""))][:30],
                    "pageText":str(d.get("pageText") or "")[:2500]
                },ensure_ascii=False)[:7000])
        prev=screen
    print("END_FISHING_SESSION")
