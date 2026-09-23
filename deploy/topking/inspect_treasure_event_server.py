from pathlib import Path
import sqlite3, json

server=Path("/opt/hamsterking-license/server.py").read_text(encoding="utf-8")
print("SERVER_TREASURE_MARKER", "TREASURE_GUIDE_CAPTURE_V1" in server)

db=sqlite3.connect("/opt/hamsterking-license/licenses.db")
db.row_factory=sqlite3.Row
try:
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
        data["payload_json"]=str(data.get("payload_json") or "")[:12000]
        data["page_text"]=str(data.get("page_text") or "")[:12000]
        print("TREASURE_SAMPLE",json.dumps(data,ensure_ascii=False))
except Exception as e:
    print("TREASURE_CAPTURE_ERROR",repr(e))
