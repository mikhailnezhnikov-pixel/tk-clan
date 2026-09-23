import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,source,path,payload_json,page_text,captured_at
                                        FROM treasure_guide_captures
                                        WHERE id BETWEEN 1008 AND 1025 ORDER BY id""")]
for r in rows:
    out={"id":r["id"],"source":r["source"],"path":r["path"],"captured_at":r["captured_at"],
         "payload_len":len(r["payload_json"] or ""),"text":re.sub(r"\s+"," ",str(r["page_text"] or "")).strip()[:1800]}
    if r["payload_json"]:
        raw=str(r["payload_json"])
        keys=[]
        try:
            obj=json.loads(raw)
            if isinstance(obj,dict): keys=list(obj.keys())
        except:pass
        out["keys"]=keys
        for term in ["treasure_search_result","choose_way","treasury","big_chest","item_treasurehunt_energy","item_treasurehunt_cur_coins"]:
            pos=raw.find(term)
            if pos>=0:
                out.setdefault("snippets",{})[term]=raw[max(0,pos-600):pos+1800]
    print("ROW",json.dumps(out,ensure_ascii=False))
