import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,source,path,payload_json,page_text,captured_at
                                        FROM treasure_guide_captures ORDER BY id""")]

print("COUNT",len(rows))
print("RECENT",json.dumps([
  {"id":r["id"],"source":r["source"],"path":r["path"],"payload_len":len(r["payload_json"] or ""),"text_len":len(r["page_text"] or ""),"captured_at":r["captured_at"]}
  for r in rows[-120:]
],ensure_ascii=False))

terms=[
 "more_money","more_food","fight_hp_up","treasure_goblin","fishing_map_finder",
 "chest_finder","chest_map_finder","map_generator","trader_maps","trader_keys","trader_rep",
 "S+","поручения питомцам","корм","золот","яйц"
]
for term in terms:
    hits=[]
    rx=re.compile(re.escape(term),re.I)
    for r in rows:
        for field in ("payload_json","page_text"):
            txt=str(r.get(field) or "")
            m=rx.search(txt)
            if not m: continue
            hits.append({
              "id":r["id"],"path":r["path"],"field":field,
              "snippet":txt[max(0,m.start()-700):m.end()+1800]
            })
            if len(hits)>=30: break
        if len(hits)>=30: break
    print("TERM",term,json.dumps(hits,ensure_ascii=False))
