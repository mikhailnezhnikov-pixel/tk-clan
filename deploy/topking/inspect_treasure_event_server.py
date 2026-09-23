import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

terms=[
"mf_shoplot_treasure_offer_pets_collection_10",
"mf_shoplot_treasure_offer_energy_collection_10",
"mf_shoplot_treasure_offer_keys_collection_10",
"mf_shoplot_treasure_offer_maps_golden_berries_10"
]
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures
                                        WHERE payload_json LIKE '%mf_shoplot_treasure_offer_%'
                                        ORDER BY id DESC LIMIT 120""")]
def walk(v,path="$",depth=0,out=None):
    out=out if out is not None else []
    if depth>18:return out
    if isinstance(v,dict):
        oid=str(v.get("id") or "")
        if oid in terms:
            out.append({"path":path,"obj":v})
        for k,val in v.items():
            if isinstance(val,(dict,list)):walk(val,path+"."+str(k),depth+1,out)
    elif isinstance(v,list):
        for i,val in enumerate(v[:10000]):
            if isinstance(val,(dict,list)):walk(val,path+f"[{i}]",depth+1,out)
    return out
found=[]
for r in rows:
    try:obj=json.loads(r["payload_json"])
    except:continue
    for x in walk(obj):
        found.append({"capture":r["id"],"capture_path":r["path"],**x})
print("OFFER_LOTS",json.dumps(found,ensure_ascii=False))
