import importlib.util,json,re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

rx=re.compile(r"^mf_shoplot_treasure_offer_(?:pets_collection_10|energy_collection_10|keys_collection_10|maps_golden_berries_10)$")

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE path LIKE '/shop/view#treasure-%'
                                        ORDER BY id DESC LIMIT 200""")]

found={}
captures=[]
for r in rows:
    try:
        obj=json.loads(r.get("payload_json") or "{}")
    except Exception:
        continue
    for row in obj.get("rows",[]) if isinstance(obj,dict) else []:
        payload=row.get("payload") if isinstance(row,dict) else None
        lot_id=str(payload.get("id") or "") if isinstance(payload,dict) else ""
        if not rx.match(lot_id):
            continue
        captures.append({
            "capture":r.get("id"),
            "captured_at":r.get("captured_at"),
            "path":r.get("path"),
            "lot_id":lot_id,
            "payload":payload
        })
        if lot_id not in found:
            found[lot_id]=captures[-1]

print("BUNDLE_PRIORITY_LATEST",json.dumps(found,ensure_ascii=False))
print("BUNDLE_PRIORITY_ALL",json.dumps(captures[:40],ensure_ascii=False))
