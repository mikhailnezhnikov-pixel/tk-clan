import importlib.util,sqlite3,json,time

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_runtime_smoke_capture_schema()

db=sqlite3.connect(str(server.DB_PATH))
db.row_factory=sqlite3.Row
now=int(time.time())

versions=[dict(r) for r in db.execute("""SELECT script_version,COUNT(*) AS devices,MAX(last_seen) AS last_seen
                                       FROM devices
                                       GROUP BY script_version
                                       ORDER BY last_seen DESC
                                       LIMIT 20""")]
for row in versions:
    row["age_s"]=now-int(row.get("last_seen") or 0)
print("DEVICE_VERSIONS",json.dumps(versions,ensure_ascii=False))

rows=[dict(r) for r in db.execute("""SELECT id,script_version,revision,summary_json,events_json,captured_at
                                    FROM runtime_smoke_captures
                                    ORDER BY captured_at DESC,id DESC LIMIT 20""")]
print("RUNTIME_SMOKE_ROWS",len(rows))
for row in rows:
    summary=json.loads(row.get("summary_json") or "{}")
    events=json.loads(row.get("events_json") or "[]")
    print("RUNTIME_SMOKE_ROW",json.dumps({
        "id":row.get("id"),
        "script_version":row.get("script_version"),
        "revision":row.get("revision"),
        "age_s":now-int(row.get("captured_at") or 0),
        "summary":summary,
        "event_types":[str(e.get("type") or "") for e in events[-24:]]
    },ensure_ascii=False))
