import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

need=[
 "mf_shoplot_treasure_offer_pets_collection_10",
 "mf_shoplot_treasure_offer_energy_collection_10",
 "mf_shoplot_treasure_offer_keys_collection_10",
 "mf_shoplot_treasure_offer_maps_golden_berries_10"
]

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures
                                        WHERE payload_json<>'' ORDER BY id DESC""")]

for term in need:
    hits=[]
    for r in rows:
        raw=str(r["payload_json"] or "")
        pos=raw.find(term)
        if pos<0:continue
        hits.append({"id":r["id"],"path":r["path"],"snippet":raw[max(0,pos-1000):pos+6500]})
        if len(hits)>=8:break
    print("BUNDLE",term,json.dumps(hits,ensure_ascii=False))
