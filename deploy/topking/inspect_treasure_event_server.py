import importlib.util,json,re,time

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

wanted={
 "mf_shoplot_treasure_offer_pets_collection_10",
 "mf_shoplot_treasure_offer_energy_collection_10",
 "mf_shoplot_treasure_offer_keys_collection_10",
 "mf_shoplot_treasure_offer_maps_golden_berries_10",
}
now=int(time.time())

def walk(value,out,path="$"):
    if isinstance(value,dict):
        ident=str(value.get("id") or "")
        if ident in wanted:
            out.append({"path":path,"value":value})
        for k,v in value.items():
            walk(v,out,path+"."+str(k))
    elif isinstance(value,list):
        for i,v in enumerate(value):
            walk(v,out,path+"["+str(i)+"]")

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,player_id,path,payload_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE source='api' AND (
                                          payload_json LIKE '%mf_shoplot_treasure_offer_pets_collection_10%' OR
                                          payload_json LIKE '%mf_shoplot_treasure_offer_energy_collection_10%' OR
                                          payload_json LIKE '%mf_shoplot_treasure_offer_keys_collection_10%' OR
                                          payload_json LIKE '%mf_shoplot_treasure_offer_maps_golden_berries_10%'
                                        )
                                        ORDER BY captured_at DESC,id DESC LIMIT 40""")]

print("NOW",now)
print("BUNDLE_API_MATCH_ROWS",len(rows))
seen=set()
for row in rows:
    payload=str(row.get("payload_json") or "")
    try:
        obj=json.loads(payload)
    except Exception as e:
        print("PARSE_ERROR",row.get("id"),repr(e),len(payload))
        continue
    found=[]
    walk(obj,found)
    compact=[]
    for item in found:
        ident=str(item["value"].get("id") or "")
        if ident in seen:
            continue
        seen.add(ident)
        compact.append(item)
    if compact:
        print("BUNDLE_API_MATCH",json.dumps({
            "capture_id":row.get("id"),
            "api_path":row.get("path"),
            "age_s":now-int(row.get("captured_at") or 0),
            "captured_at":row.get("captured_at"),
            "matches":compact
        },ensure_ascii=False))
    if len(seen)==len(wanted):
        break
print("FOUND_IDS",json.dumps(sorted(seen),ensure_ascii=False))
