import importlib.util, json, time
from collections import Counter

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    latest=[dict(r) for r in db.execute("""
      SELECT id,capture_key,player_id,path,payload_json,captured_at
      FROM treasure_guide_captures
      ORDER BY id DESC
      LIMIT 500
    """)]
    trace_like=[dict(r) for r in db.execute("""
      SELECT id,capture_key,player_id,path,payload_json,captured_at
      FROM treasure_guide_captures
      WHERE capture_key LIKE '%trace%'
         OR path LIKE '%trace%'
         OR payload_json LIKE '%treasure-run-trace%'
      ORDER BY id DESC
      LIMIT 200
    """)]

def classify(row):
    payload=row.get("payload_json") or ""
    schema=""
    session=""
    run_index=None
    revision=""
    try:
        obj=json.loads(payload)
        if isinstance(obj,dict):
            schema=str(obj.get("schema") or "")
            session=str(obj.get("session_id") or "")
            run_index=obj.get("run_index")
            revision=str(obj.get("revision") or "")
    except Exception:
        pass
    return {
      "id":row.get("id"),
      "capture_key":row.get("capture_key"),
      "player_id":row.get("player_id"),
      "path":row.get("path"),
      "captured_at":str(row.get("captured_at") or ""),
      "schema":schema,
      "session_id":session,
      "run_index":run_index,
      "revision":revision,
      "payload_prefix":payload[:180],
    }

prefix_counts=Counter()
schema_counts=Counter()
for row in latest:
    key=str(row.get("capture_key") or "")
    prefix=key.split(":",1)[0] if ":" in key else key[:40]
    prefix_counts[prefix]+=1
    payload=row.get("payload_json") or ""
    try:
        obj=json.loads(payload)
        if isinstance(obj,dict):
            schema_counts[str(obj.get("schema") or "(none)")]+=1
    except Exception:
        schema_counts["(invalid-json)"]+=1

out={
  "generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
  "latest_count":len(latest),
  "latest_id_range":[latest[-1]["id"],latest[0]["id"]] if latest else None,
  "prefix_counts":dict(prefix_counts),
  "schema_counts":dict(schema_counts),
  "trace_like_count":len(trace_like),
  "trace_like":[classify(r) for r in trace_like[:80]],
  "latest_samples":[classify(r) for r in latest[:40]],
}
print(json.dumps(out,ensure_ascii=False,indent=2,default=str))
