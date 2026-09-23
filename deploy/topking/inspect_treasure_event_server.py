import importlib.util,sqlite3
from pathlib import Path

server_path="/opt/hamsterking-license/server.py"
source=Path(server_path).read_text(encoding="utf-8")
print("RUNTIME_SMOKE_MARKER", "RUNTIME_SMOKE_CAPTURE_V1" in source)
print("RUNTIME_SMOKE_ROUTE", "/api/v1/runtime-smoke/capture" in source)

spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
print("RUNTIME_SMOKE_SCHEMA_FN", hasattr(server,"ensure_runtime_smoke_capture_schema"))
print("SERVER_DB_PATH", getattr(server,"DB_PATH",""))
if hasattr(server,"ensure_runtime_smoke_capture_schema"):
    server.ensure_runtime_smoke_capture_schema()

db_path=str(getattr(server,"DB_PATH","") or "/opt/hamsterking-license/licenses.db")
db=sqlite3.connect(db_path)
rows=db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%smoke%' ORDER BY name").fetchall()
print("SMOKE_TABLES", [row[0] for row in rows])
row=db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='runtime_smoke_captures'").fetchone()
print("RUNTIME_SMOKE_TABLE", bool(row))
if row:
    count=db.execute("SELECT COUNT(*) FROM runtime_smoke_captures").fetchone()[0]
    print("RUNTIME_SMOKE_ROWS", count)
