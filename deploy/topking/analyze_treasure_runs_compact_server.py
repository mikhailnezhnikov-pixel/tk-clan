import importlib.util, json, re
from collections import defaultdict, Counter

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
      LIMIT 4000
    """)]

sessions=defaultdict(list)
for row in rows:
    try: payload=json.loads(row.get("payload_json") or "{}")
    except Exception: continue
    if payload.get("schema")!="treasure-run-trace-v1": continue
    sid=str(payload.get("session_id") or "")
    if sid: sessions[sid].append((row,payload))

def flatten(group):
    events=[]
    meta={}
    for row,p in sorted(group,key=lambda z:(int(z[1].get("batch") or 0),z[0]["id"])):
        meta.setdefault("run_index",p.get("run_index"))
        meta.setdefault("started_at",p.get("started_at"))
        for e in p.get("events") or []:
            if isinstance(e,dict): events.append(e)
    by={}
    for e in events:
        seq=e.get("seq")
        if seq is not None: by[int(seq)]=e
    return [by[k] for k in sorted(by)],meta

def target(e):
    d=e.get("data") if isinstance(e.get("data"),dict) else {}
    return d.get("target") if isinstance(d.get("target"),dict) else {}

all_sessions=[]
for sid,group in sessions.items():
    ev,meta=flatten(group)
    if ev:
        all_sessions.append((str(meta.get("started_at") or ""),sid,ev,meta))
all_sessions.sort(reverse=True)

for _,sid,events,meta in all_sessions[:2]:
    print(f"SESSION {sid} run_index={meta.get('run_index')} started_at={meta.get('started_at')} events={len(events)}")
    print("BOUNDARY_CANDIDATES")
    for e in events:
        typ=str(e.get("type") or "")
        d=e.get("data") if isinstance(e.get("data"),dict) else {}
        if typ=="click":
            t=target(e)
            txt=str(t.get("text") or "").replace("\n"," ")[:180]
            lot=str(t.get("lotId") or "")
            if "Начать новое путешествие" in txt or txt in ("1","Понятно") or lot.startswith("mf_treasurelot_active_"):
                if "Начать новое путешествие" in txt or txt=="1":
                    print(json.dumps({"seq":e.get("seq"),"at":e.get("at"),"screen":e.get("screen"),"kind":"click","text":txt,"lot":lot},ensure_ascii=False))
        elif typ=="network":
            path=str(d.get("path") or "")
            req=d.get("request") if isinstance(d.get("request"),dict) else {}
            if path in ("/fair/reroll","/shop/buy"):
                fair=req.get("fair_id")
                if path=="/fair/reroll" or fair=="fair_treasures":
                    print(json.dumps({
                        "seq":e.get("seq"),"at":e.get("at"),"screen":e.get("screen"),
                        "kind":"network","path":path,"status":d.get("status"),
                        "fair_id":fair,"shop_lot_id":req.get("shop_lot_id"),"slot_id":req.get("slot_id")
                    },ensure_ascii=False))
    print("SCREEN_RUNS")
    runs=[]
    cur=None
    for e in events:
        sc=str(e.get("screen") or "")
        if not sc: continue
        if cur is None or sc!=cur["screen"]:
            if cur: runs.append(cur)
            cur={"screen":sc,"start_seq":e.get("seq"),"start_at":e.get("at"),"end_seq":e.get("seq"),"end_at":e.get("at")}
        else:
            cur["end_seq"]=e.get("seq");cur["end_at"]=e.get("at")
    if cur:runs.append(cur)
    for r in runs:
        print(json.dumps(r,ensure_ascii=False))

    print("TREASURE_ACTIVE_CLICKS")
    for e in events:
        if str(e.get("type") or "")!="click" or str(e.get("screen") or "")!="treasure-map": continue
        t=target(e); lot=str(t.get("lotId") or "")
        if lot.startswith("mf_treasurelot_active_"):
            print(json.dumps({
                "seq":e.get("seq"),"at":e.get("at"),"lot":lot,
                "text":str(t.get("text") or "")[:120]
            },ensure_ascii=False))

    print("ERRORS_AND_BLOCKERS")
    for e in events:
        typ=str(e.get("type") or "")
        d=e.get("data") if isinstance(e.get("data"),dict) else {}
        if typ=="blocked-action":
            print(json.dumps({
                "seq":e.get("seq"),"at":e.get("at"),"screen":e.get("screen"),
                "type":"blocked","reason":d.get("reason"),"status":d.get("status"),
                "path":d.get("path"),"clickId":d.get("clickId")
            },ensure_ascii=False))
        elif typ=="network":
            try: status=int(d.get("status") or 0)
            except: status=0
            if status>=400:
                req=d.get("request") if isinstance(d.get("request"),dict) else {}
                resp=d.get("response") if isinstance(d.get("response"),dict) else {}
                print(json.dumps({
                    "seq":e.get("seq"),"at":e.get("at"),"screen":e.get("screen"),
                    "type":"http-error","status":status,"path":d.get("path"),
                    "fair_id":req.get("fair_id"),"shop_lot_id":req.get("shop_lot_id"),
                    "slot_id":req.get("slot_id"),"message":resp.get("message")
                },ensure_ascii=False))
    print("END_SESSION")
