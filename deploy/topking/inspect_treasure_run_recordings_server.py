import importlib.util, json, time
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
      LIMIT 1000
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
    if not sid:
        continue
    sessions[sid].append((row,payload))

def trim(value,depth=0):
    if value is None or isinstance(value,(int,float,bool)):
        return value
    if isinstance(value,str):
        return value[:2500]
    if depth>6:
        return "[depth-limit]"
    if isinstance(value,list):
        return [trim(v,depth+1) for v in value[:120]]
    if isinstance(value,dict):
        out={}
        for i,(k,v) in enumerate(value.items()):
            if i>=120: break
            if k=="pageText":
                out[k]=str(v)[:1800]
            else:
                out[k]=trim(v,depth+1)
        return out
    return str(value)[:1000]

output=[]
for sid,group in sessions.items():
    group.sort(key=lambda pair:(int(pair[1].get("batch") or 0), pair[0]["id"]))
    all_events=[]
    run_index=None
    started_at=None
    player_id=""
    capture_ids=[]
    for row,payload in group:
        run_index=run_index if run_index is not None else payload.get("run_index")
        started_at=started_at or payload.get("started_at")
        player_id=player_id or str(row.get("player_id") or "")
        capture_ids.append(row["id"])
        for event in payload.get("events") or []:
            if isinstance(event,dict):
                all_events.append(event)
    all_events.sort(key=lambda e:(int(e.get("seq") or 0),str(e.get("at") or "")))

    screens=[]
    for event in all_events:
        screen=str(event.get("screen") or "")
        if screen and (not screens or screens[-1]!=screen):
            screens.append(screen)

    clicks=[]
    network=[]
    errors=[]
    for event in all_events:
        typ=str(event.get("type") or "")
        data=event.get("data") if isinstance(event.get("data"),dict) else {}
        if typ=="click":
            target=data.get("target") if isinstance(data.get("target"),dict) else {}
            clicks.append({
                "seq":event.get("seq"),
                "at":event.get("at"),
                "screen":event.get("screen"),
                "lotId":target.get("lotId"),
                "text":str(target.get("text") or "")[:600],
                "tag":target.get("tag"),
                "x":target.get("x"),
                "y":target.get("y"),
            })
        elif typ=="network":
            row={
                "seq":event.get("seq"),
                "at":event.get("at"),
                "screen":event.get("screen"),
                "path":data.get("path"),
                "method":data.get("method"),
                "status":data.get("status"),
                "request":trim(data.get("request")),
                "response":trim(data.get("response")),
            }
            network.append(row)
            try:
                if int(data.get("status") or 0)>=400:
                    errors.append(row)
            except Exception:
                pass

    output.append({
        "session_id":sid,
        "run_index":run_index,
        "started_at":started_at,
        "player_id":player_id,
        "capture_ids":capture_ids,
        "batches":len(group),
        "events":len(all_events),
        "first_event_at":all_events[0].get("at") if all_events else None,
        "last_event_at":all_events[-1].get("at") if all_events else None,
        "screen_sequence":screens,
        "clicks":clicks,
        "network":network,
        "errors":errors,
        "trace":[trim(event) for event in all_events],
    })

output.sort(key=lambda item:str(item.get("started_at") or ""),reverse=True)
result={
    "generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
    "sessions":output[:8],
}
print(json.dumps(result,ensure_ascii=False,indent=2))
