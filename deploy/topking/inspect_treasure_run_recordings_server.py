import importlib.util, json, time
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
      LIMIT 3000
    """)]

sessions=defaultdict(list)
for row in rows:
    try:
        payload=json.loads(row.get("payload_json") or "{}")
    except Exception:
        continue
    if payload.get("schema")!="treasure-run-trace-v1":
        continue
    sid=str(payload.get("session_id") or "")
    if sid:
        sessions[sid].append((row,payload))

def scalar(value,limit=500):
    if value is None or isinstance(value,(int,float,bool)):
        return value
    if isinstance(value,str):
        return value[:limit]
    return None

def compact_request(value):
    if not isinstance(value,dict):
        return scalar(value,800)
    keys=(
        "fair_id","shop_lot_id","slot_id","id","type","action","enemy_id",
        "sword_id","target_id","choice","cost","amount","quantity"
    )
    out={}
    for key in keys:
        if key in value:
            v=scalar(value.get(key),300)
            if v is not None:
                out[key]=v
    return out

def compact_response(value):
    if not isinstance(value,dict):
        return scalar(value,400)
    out={}
    for key in ("type","message","error","code","status","success"):
        if key in value:
            v=scalar(value.get(key),400)
            if v is not None:
                out[key]=v
    return out

def compact_event(event, include_snapshot=False):
    typ=str(event.get("type") or "")
    data=event.get("data") if isinstance(event.get("data"),dict) else {}
    row={
        "seq":event.get("seq"),
        "at":event.get("at"),
        "t":event.get("t"),
        "screen":str(event.get("screen") or "")[:50],
        "type":typ[:60],
    }
    if typ=="click":
        target=data.get("target") if isinstance(data.get("target"),dict) else {}
        row.update({
            "lotId":str(target.get("lotId") or "")[:180],
            "text":str(target.get("text") or "")[:420],
            "tag":str(target.get("tag") or "")[:30],
            "x":target.get("x"),"y":target.get("y"),
            "pointerType":str(data.get("pointerType") or "")[:30],
        })
    elif typ=="network":
        row.update({
            "path":str(data.get("path") or "")[:180],
            "method":str(data.get("method") or "")[:16],
            "status":data.get("status"),
            "request":compact_request(data.get("request")),
            "response":compact_response(data.get("response")),
        })
    elif typ=="blocked-action":
        row.update({
            "reason":str(data.get("reason") or "")[:220],
            "path":str(data.get("path") or "")[:180],
            "status":data.get("status"),
        })
    elif typ=="snapshot" and include_snapshot:
        lots=data.get("lots") if isinstance(data.get("lots"),list) else []
        row["snapshot"]={
            "reason":str(data.get("reason") or "")[:80],
            "headings":[str(v)[:160] for v in (data.get("headings") or [])[:6]],
            "modals":[str(v)[:500] for v in (data.get("modals") or [])[:4]],
            "lots":[
                {
                    "lotId":str(v.get("lotId") or "")[:180],
                    "text":str(v.get("text") or "")[:260],
                }
                for v in lots[:45] if isinstance(v,dict)
            ],
        }
    elif typ not in ("snapshot",):
        small={}
        for key,value in list(data.items())[:16]:
            v=scalar(value,300)
            if v is not None:
                small[str(key)[:60]]=v
        if small:
            row["data"]=small
    return row

records=[]
for sid,group in sessions.items():
    group.sort(key=lambda pair:(int(pair[1].get("batch") or 0),pair[0]["id"]))
    events_by_seq={}
    run_index=None
    started_at=None
    player_id=""
    capture_ids=[]
    batches=set()
    revisions=set()
    for row,payload in group:
        if run_index is None:
            run_index=payload.get("run_index")
        started_at=started_at or payload.get("started_at")
        player_id=player_id or str(row.get("player_id") or "")
        capture_ids.append(row["id"])
        batches.add(int(payload.get("batch") or 0))
        if payload.get("revision"):
            revisions.add(str(payload.get("revision")))
        for event in payload.get("events") or []:
            if not isinstance(event,dict):
                continue
            try:
                seq=int(event.get("seq"))
            except Exception:
                continue
            events_by_seq[seq]=event

    events=[events_by_seq[k] for k in sorted(events_by_seq)]
    screens=[]
    transitions=[]
    last_screen=None
    for event in events:
        screen=str(event.get("screen") or "")
        if screen and screen!=last_screen:
            transitions.append({
                "seq":event.get("seq"),
                "at":event.get("at"),
                "from":last_screen,
                "to":screen,
                "event":str(event.get("type") or ""),
            })
            screens.append(screen)
            last_screen=screen

    event_counts=Counter(str(e.get("type") or "") for e in events)
    network_status=Counter()
    endpoints=Counter()
    blocked=Counter()
    for event in events:
        typ=str(event.get("type") or "")
        data=event.get("data") if isinstance(event.get("data"),dict) else {}
        if typ=="network":
            status=data.get("status")
            if status is not None:
                network_status[str(status)]+=1
            endpoint=(str(data.get("method") or "")+" "+str(data.get("path") or "")).strip()
            if endpoint:
                endpoints[endpoint]+=1
        elif typ=="blocked-action":
            blocked[str(data.get("reason") or "(unknown)")]+=1

    records.append({
        "_events_raw":events,
        "session_id":sid,
        "run_index":run_index,
        "started_at":started_at,
        "player_id":player_id,
        "capture_id_min":min(capture_ids) if capture_ids else None,
        "capture_id_max":max(capture_ids) if capture_ids else None,
        "captures":len(capture_ids),
        "batches":len(batches),
        "batch_min":min(batches) if batches else None,
        "batch_max":max(batches) if batches else None,
        "revisions":sorted(revisions),
        "events":len(events),
        "first_event_at":events[0].get("at") if events else None,
        "last_event_at":events[-1].get("at") if events else None,
        "screen_sequence":screens,
        "screen_transitions":transitions[:160],
        "event_type_counts":dict(event_counts),
        "network_status_counts":dict(network_status),
        "endpoint_counts":dict(endpoints),
        "blocked_reason_counts":dict(blocked),
    })

records.sort(key=lambda item:(str(item.get("started_at") or ""),int(item.get("run_index") or 0)),reverse=True)

summary=[]
for rec in records[:16]:
    summary.append({k:v for k,v in rec.items() if k!="_events_raw"})

latest_detail=None
if records:
    rec=records[0]
    raw=rec["_events_raw"]
    detail=[]
    last_snapshot_screen=None
    # Keep every actionable event. Keep only snapshots that introduce a screen,
    # a modal, or a useful state transition. This makes the file API-readable.
    for event in raw:
        typ=str(event.get("type") or "")
        screen=str(event.get("screen") or "")
        data=event.get("data") if isinstance(event.get("data"),dict) else {}
        if typ!="snapshot":
            detail.append(compact_event(event))
            continue
        modals=data.get("modals") if isinstance(data.get("modals"),list) else []
        reason=str(data.get("reason") or "")
        important=(screen!=last_snapshot_screen) or bool(modals) or reason in (
            "session-start","session-stop","after-network","after-click-settle"
        )
        if important:
            detail.append(compact_event(event,include_snapshot=True))
            last_snapshot_screen=screen
        if len(detail)>=2200:
            break

    latest_detail={
        "session_id":rec["session_id"],
        "run_index":rec["run_index"],
        "started_at":rec["started_at"],
        "player_id":rec["player_id"],
        "events_total":rec["events"],
        "events_exported":len(detail),
        "screen_sequence":rec["screen_sequence"],
        "timeline":detail,
    }

result={
    "schema":"treasure-run-recordings-review-v3",
    "generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
    "source_trace_rows":len(rows),
    "session_count":len(records),
    "sessions":summary,
    "latest_detail":latest_detail,
}
print(json.dumps(result,ensure_ascii=False,indent=2))
