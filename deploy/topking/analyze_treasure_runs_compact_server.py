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

    print("SECOND_MAP_DEEP_TRACE")
    second_start_seq=729
    fair_counts=Counter()
    for e in events:
        try: seq=int(e.get("seq") or 0)
        except: seq=0
        if seq<second_start_seq: continue
        typ=str(e.get("type") or "")
        d=e.get("data") if isinstance(e.get("data"),dict) else {}
        if typ=="click":
            t=target(e)
            lot=str(t.get("lotId") or "")
            txt=str(t.get("text") or "").replace("\n"," ")[:160]
            if lot.startswith("mf_") or txt in ("Понятно","1","10","20","40") or "Покинуть" in txt or "Начать новое путешествие" in txt:
                print(json.dumps({
                    "seq":seq,"at":e.get("at"),"screen":e.get("screen"),
                    "type":"click","lot":lot,"text":txt
                },ensure_ascii=False))
        elif typ=="network":
            path=str(d.get("path") or "")
            req=d.get("request") if isinstance(d.get("request"),dict) else {}
            fair=str(req.get("fair_id") or "")
            if fair: fair_counts[fair]+=1
            if path in ("/shop/buy","/fair/reroll"):
                print(json.dumps({
                    "seq":seq,"at":e.get("at"),"screen":e.get("screen"),
                    "type":"network","path":path,"status":d.get("status"),
                    "fair_id":fair,"shop_lot_id":req.get("shop_lot_id"),
                    "slot_id":req.get("slot_id")
                },ensure_ascii=False))
    print("SECOND_MAP_FAIR_COUNTS "+json.dumps(dict(fair_counts),ensure_ascii=False))
    print("LABYRINTH_GAP_STATES")
    last_state=None
    printed=0
    for e in events:
        try: seq=int(e.get("seq") or 0)
        except: seq=0
        if seq<850 or seq>1428: continue
        typ=str(e.get("type") or "")
        d=e.get("data") if isinstance(e.get("data"),dict) else {}
        if typ=="snapshot":
            headings=tuple(str(x)[:180] for x in (d.get("headings") or [])[:6])
            modals=tuple(str(x)[:220] for x in (d.get("modals") or [])[:4])
            lots=[]
            for item in (d.get("lots") or []):
                if isinstance(item,dict):
                    lid=str(item.get("lotId") or "")
                    txt=str(item.get("text") or "").replace("\n"," ")[:100]
                    if lid or txt:
                        lots.append((lid,txt))
            key=(headings,modals,tuple(lots[:24]))
            if key!=last_state and printed<80:
                print(json.dumps({
                    "seq":seq,"at":e.get("at"),"screen":e.get("screen"),
                    "headings":list(headings),"modals":list(modals),
                    "lots":[{"lotId":lid,"text":txt} for lid,txt in lots[:24]],
                    "page":str(d.get("pageText") or "").replace("\n"," ")[:500]
                },ensure_ascii=False))
                printed+=1
                last_state=key
        elif typ=="click":
            t=target(e)
            lid=str(t.get("lotId") or "")
            txt=str(t.get("text") or "").replace("\n"," ")[:220]
            if lid or txt:
                print(json.dumps({
                    "seq":seq,"at":e.get("at"),"screen":e.get("screen"),
                    "click_lot":lid,"click_text":txt
                },ensure_ascii=False))

    print("FIRST_MAP_BOSS_TRACE")
    for e in events:
        try: seq=int(e.get("seq") or 0)
        except: seq=0
        if seq<555 or seq>595: continue
        typ=str(e.get("type") or "")
        d=e.get("data") if isinstance(e.get("data"),dict) else {}
        if typ=="click":
            t=target(e)
            print(json.dumps({
                "seq":seq,"at":e.get("at"),"screen":e.get("screen"),
                "type":"click","lot":str(t.get("lotId") or ""),
                "text":str(t.get("text") or "").replace("\n"," ")[:220]
            },ensure_ascii=False))
        elif typ=="network":
            req=d.get("request") if isinstance(d.get("request"),dict) else {}
            print(json.dumps({
                "seq":seq,"at":e.get("at"),"screen":e.get("screen"),
                "type":"network","path":d.get("path"),"status":d.get("status"),
                "fair_id":req.get("fair_id"),"shop_lot_id":req.get("shop_lot_id"),"slot_id":req.get("slot_id")
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
    print("RECOVERY_GENERAL_CAPTURES")
    try:
        with server.db_session() as db:
            extra=[dict(r) for r in db.execute("""
              SELECT id,capture_key,player_id,source,path,payload_json,page_text,captured_at
              FROM treasure_guide_captures
              WHERE player_id=?
                AND id BETWEEN 14700 AND 15080
                AND capture_key NOT LIKE 'trace:%'
              ORDER BY id
            """,(str(group[0][0].get("player_id") or ""),))]
        for row in extra:
            payload={}
            try: payload=json.loads(row.get("payload_json") or "{}")
            except Exception: payload={}
            compact={}
            if isinstance(payload,dict):
                for key in ["url","path","method","status","fair_id","shop_lot_id","slot_id","type","message","error","result","data"]:
                    if key in payload:
                        val=payload.get(key)
                        if isinstance(val,(dict,list)):
                            val=str(val)[:700]
                        compact[key]=val
                # Common nested request/response shapes.
                for nest in ["request","response","body"]:
                    val=payload.get(nest)
                    if isinstance(val,dict):
                        compact[nest]={k:val.get(k) for k in ["fair_id","shop_lot_id","slot_id","type","message","status"] if k in val}
            text_preview=str(row.get("page_text") or "").replace("\n"," ")[:500]
            print(json.dumps({
                "id":row.get("id"),"captured_at":row.get("captured_at"),
                "source":row.get("source"),"path":row.get("path"),
                "capture_key":str(row.get("capture_key") or "")[:180],
                "payload":compact,"page":text_preview
            },ensure_ascii=False))
    except Exception as exc:
        print("RECOVERY_ERROR "+repr(exc))
    print("RECOVERY_RAW_TARGETS")
    try:
        with server.db_session() as db:
            rawrows=[dict(r) for r in db.execute("""
              SELECT id,path,payload_json,captured_at
              FROM treasure_guide_captures
              WHERE id BETWEEN 14902 AND 14914
              ORDER BY id
            """)]
        for row in rawrows:
            print(json.dumps({
                "id":row.get("id"),"captured_at":row.get("captured_at"),"path":row.get("path"),
                "raw":str(row.get("payload_json") or "")[:5000]
            },ensure_ascii=False))
    except Exception as exc:
        print("RECOVERY_RAW_ERROR "+repr(exc))
    print("END_SESSION")
