import importlib.util, json, time, re
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

def compact_obj(value, depth=0):
    if value is None or isinstance(value,(int,float,bool)):
        return value
    if isinstance(value,str):
        return value[:700]
    if depth>=4:
        return "[trimmed]"
    if isinstance(value,list):
        return [compact_obj(v,depth+1) for v in value[:30]]
    if isinstance(value,dict):
        wanted={}
        important_keys=[
            "id","lot_id","shop_lot_id","fair_id","map_id","treasure_map_id","slot",
            "slot_id","position","x","y","type","kind","status","success","message","error",
            "code","result","reward","rewards","cost","price","amount","quantity","count",
            "currency","balance","resource","resources","item","items","data","state"
        ]
        for k in important_keys:
            if k in value:
                wanted[k]=compact_obj(value[k],depth+1)
        if wanted:
            return wanted
        for i,(k,v) in enumerate(value.items()):
            if i>=15: break
            wanted[k]=compact_obj(v,depth+1)
        return wanted
    return str(value)[:700]

def event_screen(event):
    return str(event.get("screen") or "")

summaries=[]
for sid,group in sessions.items():
    group.sort(key=lambda pair:(int(pair[1].get("batch") or 0), pair[0]["id"]))
    events=[]
    started_at=None
    run_index=None
    player_id=""
    capture_ids=[]
    for row,payload in group:
        started_at=started_at or payload.get("started_at")
        run_index=run_index if run_index is not None else payload.get("run_index")
        player_id=player_id or str(row.get("player_id") or "")
        capture_ids.append(row["id"])
        for event in payload.get("events") or []:
            if isinstance(event,dict):
                events.append(event)

    # Deduplicate by seq, keeping latest copy if batching retried.
    by_seq={}
    noseq=[]
    for event in events:
        seq=event.get("seq")
        if seq is None:
            noseq.append(event)
        else:
            by_seq[int(seq)]=event
    events=[by_seq[k] for k in sorted(by_seq)] + noseq
    events.sort(key=lambda e:(int(e.get("seq") or 10**12),str(e.get("at") or "")))

    completed=any(str(e.get("type") or "")=="session-stop" for e in events)
    screens=[]
    screen_transitions=[]
    prev=""
    for e in events:
        sc=event_screen(e)
        if sc and sc!=prev:
            screens.append(sc)
            screen_transitions.append({
                "seq":e.get("seq"),"at":e.get("at"),"from":prev or None,"to":sc,"event":e.get("type")
            })
            prev=sc

    type_counts=Counter(str(e.get("type") or "") for e in events)
    status_counts=Counter()
    endpoint_counts=Counter()
    blocked_counts=Counter()
    clicks=[]
    networks=[]
    blockers=[]
    snapshots=[]
    timeline=[]

    for e in events:
        typ=str(e.get("type") or "")
        data=e.get("data") if isinstance(e.get("data"),dict) else {}
        base={"seq":e.get("seq"),"at":e.get("at"),"t":e.get("t"),"screen":event_screen(e),"type":typ}

        if typ=="click":
            target=data.get("target") if isinstance(data.get("target"),dict) else {}
            item={
                **base,
                "clickId":data.get("clickId"),
                "lotId":str(target.get("lotId") or "")[:220],
                "text":str(target.get("text") or "")[:350],
                "tag":target.get("tag"),
                "disabled":target.get("disabled"),
                "ariaDisabled":target.get("ariaDisabled"),
                "x":target.get("x"),"y":target.get("y")
            }
            clicks.append(item)
            timeline.append(item)

        elif typ=="network":
            path=str(data.get("path") or "")
            method=str(data.get("method") or "GET")
            try: status=int(data.get("status") or 0)
            except Exception: status=0
            status_counts[str(status)]+=1
            endpoint_counts[f"{method} {path}"]+=1
            item={
                **base,
                "path":path,
                "method":method,
                "status":status,
                "request":compact_obj(data.get("request")),
                "response":compact_obj(data.get("response"))
            }
            networks.append(item)
            if method!="GET" or status>=400:
                timeline.append(item)

        elif typ=="blocked-action":
            reason=str(data.get("reason") or "blocked")
            blocked_counts[reason]+=1
            item={
                **base,
                "reason":reason,
                "phase":data.get("phase"),
                "clickId":data.get("clickId"),
                "path":data.get("path"),
                "method":data.get("method"),
                "status":data.get("status"),
                "target":compact_obj(data.get("target")),
                "modals":compact_obj(data.get("modals")),
                "response":compact_obj(data.get("response"))
            }
            blockers.append(item)
            timeline.append(item)

        elif typ in ("session-start","session-resume","session-stop"):
            timeline.append({**base,"data":compact_obj(data)})

        elif typ=="snapshot":
            reason=str(data.get("reason") or "")
            lots=data.get("lots") if isinstance(data.get("lots"),list) else []
            modals=data.get("modals") if isinstance(data.get("modals"),list) else []
            blockers_raw=data.get("blockers") if isinstance(data.get("blockers"),list) else []
            snap={
                **base,
                "reason":reason,
                "headings":[str(x)[:250] for x in (data.get("headings") or [])[:8]],
                "modals":[str(x)[:500] for x in modals[:6]],
                "blockers":compact_obj(blockers_raw),
                "lots":[
                    {
                        "lotId":str(x.get("lotId") or "")[:220],
                        "text":str(x.get("text") or "")[:240],
                        "x":x.get("x"),"y":x.get("y")
                    }
                    for x in lots[:60] if isinstance(x,dict)
                ]
            }
            snapshots.append(snap)

    # Keep snapshots only around transitions / first occurrence of each screen fingerprint to avoid giant result.
    selected_snaps=[]
    last_key=None
    for snap in snapshots:
        key=(
            snap["screen"],
            tuple(x["lotId"] for x in snap["lots"][:20]),
            tuple(snap["modals"][:3])
        )
        if key!=last_key:
            selected_snaps.append(snap)
            last_key=key
        if len(selected_snaps)>=80:
            break

    # Identify likely map-cell clicks and mini-game actions.
    map_clicks=[c for c in clicks if c.get("screen")=="treasure-map"]
    minigame_clicks=[c for c in clicks if c.get("screen") in ("battle","fishing","trader","lights","chests","labyrinth")]
    error_networks=[n for n in networks if int(n.get("status") or 0)>=400]

    # Compact the timeline to meaningful events only, capped.
    timeline.sort(key=lambda x:(int(x.get("seq") or 10**12),str(x.get("at") or "")))
    if len(timeline)>500:
        timeline=timeline[:250]+[{"type":"...","note":f"{len(timeline)-500} middle events omitted"}]+timeline[-250:]

    summaries.append({
        "session_id":sid,
        "run_index":run_index,
        "started_at":started_at,
        "player_id":player_id,
        "completed":completed,
        "capture_ids":capture_ids,
        "batches":len(group),
        "events":len(events),
        "first_event_at":events[0].get("at") if events else None,
        "last_event_at":events[-1].get("at") if events else None,
        "duration_ms":(
            (int(events[-1].get("t") or 0)-int(events[0].get("t") or 0))
            if len(events)>=2 else 0
        ),
        "event_type_counts":dict(type_counts),
        "screen_sequence":screens,
        "screen_transitions":screen_transitions,
        "network_status_counts":dict(status_counts),
        "endpoint_counts":dict(endpoint_counts),
        "blocked_reason_counts":dict(blocked_counts),
        "map_clicks":map_clicks,
        "minigame_click_count":len(minigame_clicks),
        "errors":error_networks,
        "blockers":blockers,
        "snapshots_compact":selected_snaps,
        "timeline":timeline
    })

summaries.sort(key=lambda s:str(s.get("started_at") or ""),reverse=True)
completed=[s for s in summaries if s.get("completed")]
selected=(completed[:2] if len(completed)>=2 else summaries[:2])

print(json.dumps({
    "generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
    "session_count_found":len(summaries),
    "completed_session_count":len(completed),
    "selected_two_latest":selected
},ensure_ascii=False,indent=2))
