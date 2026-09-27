import importlib.util, json, time
from collections import defaultdict, Counter

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

# Read enough trace rows to cover several recent runs, but export them compactly.
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
      SELECT id,capture_key,player_id,path,payload_json,captured_at
      FROM treasure_guide_captures
      WHERE capture_key LIKE 'trace:%'
         OR path LIKE 'trace/%'
         OR payload_json LIKE '%"schema":"treasure-run-trace-v1"%'
      ORDER BY id DESC
      LIMIT 6000
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

def scalar(value,limit=600):
    if value is None or isinstance(value,(int,float,bool)):
        return value
    if isinstance(value,str):
        return value[:limit]
    return None

def request_compact(value):
    if not isinstance(value,dict):
        return scalar(value,1200)
    out={}
    # Keep fields that explain what action the client actually sent.
    wanted=(
      "fair_id","shop_lot_id","slot_id","id","type","action","enemy_id",
      "sword_id","target_id","choice","cost","amount","quantity"
    )
    for key in wanted:
        if key in value:
            v=scalar(value.get(key),500)
            if v is not None:
                out[key]=v
    if not out:
        for key,value2 in list(value.items())[:16]:
            v=scalar(value2,300)
            if v is not None:
                out[str(key)[:80]]=v
    return out

def response_compact(value):
    if not isinstance(value,dict):
        return scalar(value,800)
    out={}
    for key in ("type","message","error","code","status","success"):
        if key in value:
            v=scalar(value.get(key),600)
            if v is not None:
                out[key]=v
    # Preserve a few small state-like fields, never the full giant game state.
    for key in ("fair","shop_lot","reward","rewards","result"):
        if key not in value:
            continue
        v=value.get(key)
        try:
            text=json.dumps(v,ensure_ascii=False,separators=(",",":"))
        except Exception:
            continue
        if len(text)<=1800:
            out[key]=v
    return out

def target_compact(data):
    target=data.get("target") if isinstance(data.get("target"),dict) else {}
    return {
      "lotId":str(target.get("lotId") or "")[:220],
      "text":str(target.get("text") or "")[:700],
      "tag":str(target.get("tag") or "")[:40],
      "disabled":bool(target.get("disabled")) if "disabled" in target else None,
      "ariaDisabled":str(target.get("ariaDisabled") or "")[:40],
      "x":target.get("x"),
      "y":target.get("y"),
      "w":target.get("w"),
      "h":target.get("h"),
    }

def snapshot_compact(data):
    lots=[]
    raw_lots=data.get("lots") if isinstance(data.get("lots"),list) else []
    for row in raw_lots[:80]:
        if not isinstance(row,dict):
            continue
        lots.append({
          "lotId":str(row.get("lotId") or "")[:220],
          "text":str(row.get("text") or "")[:380],
          "x":row.get("x"),"y":row.get("y"),"w":row.get("w"),"h":row.get("h"),
        })
    return {
      "reason":str(data.get("reason") or "")[:120],
      "screen":str(data.get("screen") or "")[:60],
      "headings":[str(v)[:220] for v in (data.get("headings") or [])[:10]],
      "modals":[str(v)[:1000] for v in (data.get("modals") or [])[:6]],
      "lots":lots,
      "pageText":str(data.get("pageText") or "")[:1800],
    }

def event_compact(event):
    typ=str(event.get("type") or "")
    data=event.get("data") if isinstance(event.get("data"),dict) else {}
    row={
      "seq":event.get("seq"),
      "at":event.get("at"),
      "t":event.get("t"),
      "screen":str(event.get("screen") or "")[:60],
      "type":typ[:80],
    }
    if typ=="click":
        row.update(target_compact(data))
        row["pointerType"]=str(data.get("pointerType") or "")[:40]
    elif typ=="network":
        row.update({
          "path":str(data.get("path") or "")[:240],
          "method":str(data.get("method") or "")[:20],
          "status":data.get("status"),
          "request":request_compact(data.get("request")),
          "response":response_compact(data.get("response")),
        })
    elif typ=="snapshot":
        row["snapshot"]=snapshot_compact(data)
    elif typ=="blocked-action":
        row["reason"]=str(data.get("reason") or "")[:300]
        row["path"]=str(data.get("path") or "")[:220]
        row["status"]=data.get("status")
    else:
        compact={}
        for key,value in list(data.items())[:24]:
            v=scalar(value,500)
            if v is not None:
                compact[str(key)[:80]]=v
        if compact:
            row["data"]=compact
    return row

output=[]
for sid,group in sessions.items():
    # Duplicate batches can exist when a retry used the same batch number but a
    # different capture hash. De-duplicate events by seq after merging all rows.
    group.sort(key=lambda pair:(int(pair[1].get("batch") or 0), pair[0]["id"]))
    events_by_seq={}
    run_index=None
    started_at=None
    player_id=""
    capture_ids=[]
    batches=set()
    revisions=set()
    for row,payload in group:
        run_index=run_index if run_index is not None else payload.get("run_index")
        started_at=started_at or payload.get("started_at")
        player_id=player_id or str(row.get("player_id") or "")
        capture_ids.append(row["id"])
        batches.add(int(payload.get("batch") or 0))
        if payload.get("revision"):
            revisions.add(str(payload.get("revision")))
        for event in payload.get("events") or []:
            if not isinstance(event,dict):
                continue
            seq=event.get("seq")
            if seq is None:
                continue
            try:
                key=int(seq)
            except Exception:
                continue
            events_by_seq[key]=event

    all_events=[events_by_seq[k] for k in sorted(events_by_seq)]
    screens=[]
    for event in all_events:
        screen=str(event.get("screen") or "")
        if screen and (not screens or screens[-1]!=screen):
            screens.append(screen)

    event_counts=Counter(str(e.get("type") or "") for e in all_events)
    network_status=Counter()
    endpoint_counts=Counter()
    error_count=0
    compact_events=[]
    for event in all_events:
        row=event_compact(event)
        compact_events.append(row)
        if row.get("type")=="network":
            status=row.get("status")
            if status is not None:
                network_status[str(status)]+=1
                try:
                    if int(status)>=400:
                        error_count+=1
                except Exception:
                    pass
            endpoint_counts[(str(row.get("method") or "")+" "+str(row.get("path") or "")).strip()]+=1

    output.append({
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
      "events":len(all_events),
      "first_event_at":all_events[0].get("at") if all_events else None,
      "last_event_at":all_events[-1].get("at") if all_events else None,
      "screen_sequence":screens,
      "event_type_counts":dict(event_counts),
      "network_status_counts":dict(network_status),
      "endpoint_counts":dict(endpoint_counts),
      "error_count":error_count,
      "trace":compact_events,
    })

output.sort(key=lambda item:(str(item.get("started_at") or ""),int(item.get("run_index") or 0)),reverse=True)

# The file intentionally stays reviewable through GitHub/API instead of becoming
# a multi-megabyte dump of full /shop/buy responses.
result={
  "schema":"treasure-run-recordings-compact-v2",
  "generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
  "source_trace_rows":len(rows),
  "session_count":len(output),
  "sessions":output[:12],
}
print(json.dumps(result,ensure_ascii=False,indent=2))
