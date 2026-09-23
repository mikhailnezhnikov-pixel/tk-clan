import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures
                                        WHERE path LIKE '/shop/view#treasure-%'
                                        ORDER BY id""")]

rx=re.compile(r"(?:treasury|lights|fishing|chests|trader|fight|treasure)",re.I)
out={}
for r in rows:
    try: obj=json.loads(r["payload_json"] or "{}")
    except: continue
    arr=obj.get("rows",[]) if isinstance(obj,dict) else []
    for item in arr if isinstance(arr,list) else []:
        payload=item.get("payload") if isinstance(item,dict) else None
        if not isinstance(payload,dict): continue
        oid=str(payload.get("id") or "")
        if not oid or "achievement" in oid.lower() or not rx.search(oid): continue
        if "lot_view" not in payload and "cost" not in payload: continue
        out.setdefault(oid,{
          "id":oid,
          "cost":payload.get("cost"),
          "lot_view":payload.get("lot_view"),
          "source":r["path"],
          "json_path":item.get("path")
        })
print("NON_ACHIEVEMENT_LOTS",json.dumps(list(out.values()),ensure_ascii=False,separators=(",",":")))
