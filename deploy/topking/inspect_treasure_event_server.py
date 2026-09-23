import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

rx=re.compile(r"^mf_shoplot_treasure_offer_(?:pets_collection_10|energy_collection_10|keys_collection_10|maps_golden_berries_10)$")
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,captured_at FROM treasure_guide_captures
                                        WHERE path LIKE '/shop/view#treasure-%'
                                        ORDER BY id DESC LIMIT 80""")]
out=[]
for r in rows:
    try:obj=json.loads(r["payload_json"])
    except:continue
    for row in obj.get("rows",[]) if isinstance(obj,dict) else []:
        p=row.get("payload") if isinstance(row,dict) else None
        if isinstance(p,dict) and rx.match(str(p.get("id") or "")):
            out.append({"capture":r["id"],"captured_at":r["captured_at"],"payload":p})
print("BUNDLE_PRIORITY",json.dumps(out,ensure_ascii=False))
