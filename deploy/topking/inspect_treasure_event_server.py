import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

rx=re.compile(r"^minigame_(?:fight|fishing|chests|lights|trader|all_maps|mines|keys)_achievement_")
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures
                                        WHERE path LIKE '/shop/view#treasure-%'
                                        ORDER BY id DESC LIMIT 120""")]

out={}
for r in rows:
    try:obj=json.loads(r["payload_json"])
    except:continue
    for row in obj.get("rows",[]) if isinstance(obj,dict) else []:
        p=row.get("payload") if isinstance(row,dict) else None
        if not isinstance(p,dict):continue
        pid=str(p.get("id") or "")
        if rx.match(pid) and pid not in out:
            out[pid]={
              "id":pid,
              "cost":p.get("cost"),
              "lot_view":p.get("lot_view"),
              "capture":r["id"]
            }
print("ACH_LOTS",json.dumps(list(out.values()),ensure_ascii=False))
