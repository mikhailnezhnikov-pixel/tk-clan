from pathlib import Path
import re, json, sqlite3, glob, os, importlib.util

server_path="/opt/hamsterking-license/server.py"
source=Path(server_path).read_text(encoding="utf-8")
print("SERVER_TREASURE_MARKER", "TREASURE_GUIDE_CAPTURE_V1" in source)
for pattern in [r"DB_PATH\s*=.*", r"SQLITE[^\n]*", r"def db_session\(.*?\n(?:    .*\n){0,20}"]:
    print("PATTERN",pattern)
    for m in re.finditer(pattern,source,re.S|re.M):
        print(m.group(0)[:4000])

print("DB_FILES",json.dumps([
    {"path":p,"size":os.path.getsize(p)} for p in glob.glob("/opt/hamsterking-license/**/*.db",recursive=True)
],ensure_ascii=False))

spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
print("IMPORTED",True)
if hasattr(server,"DB_PATH"):
    print("SERVER_DB_PATH",getattr(server,"DB_PATH"))
if hasattr(server,"ensure_treasure_guide_capture_schema"):
    server.ensure_treasure_guide_capture_schema()
    print("ENSURE_TREASURE_SCHEMA",True)
try:
    with server.db_session() as db:
        tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        print("TABLES",json.dumps(tables,ensure_ascii=False))
        if "treasure_guide_captures" in tables:
            rows=[dict(r) for r in db.execute("""SELECT id,source,path,length(payload_json) AS payload_len,
                                                       length(page_text) AS text_len,assets_json,captured_at
                                                FROM treasure_guide_captures
                                                ORDER BY captured_at DESC,id DESC LIMIT 80""")]
            print("TREASURE_CAPTURE_COUNT",len(rows))
            print("TREASURE_CAPTURES",json.dumps(rows,ensure_ascii=False))
            for row in db.execute("""SELECT id,source,path,payload_json,page_text,assets_json,captured_at
                                     FROM treasure_guide_captures
                                     ORDER BY captured_at DESC,id DESC LIMIT 12"""):
                data=dict(row)
                data["payload_json"]=str(data.get("payload_json") or "")[:16000]
                data["page_text"]=str(data.get("page_text") or "")[:16000]
                print("TREASURE_SAMPLE",json.dumps(data,ensure_ascii=False))
except Exception as e:
    print("TREASURE_CAPTURE_ERROR",repr(e))
