import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

terms=["bp_event_minigame","bp_event_minigame_line_free","bp_event_minigame_line_paid_01","bp_event_minigame_line_paid_02"]
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures
                                        WHERE payload_json<>'' ORDER BY id""")]

for term in terms:
    out=[]
    for r in rows:
        raw=str(r["payload_json"] or "")
        if term not in raw:continue
        try:obj=json.loads(raw)
        except:continue
        stack=[("$",obj,0)]
        while stack and len(out)<80:
            path,v,depth=stack.pop()
            if depth>18:continue
            if isinstance(v,dict):
                blob=json.dumps(v,ensure_ascii=False,separators=(",",":"))
                if term in blob and len(blob)<30000:
                    if any(k in v for k in ("levels","rewards","line_id","score_step","lot_view","id")):
                        out.append({"capture":r["id"],"capture_path":r["path"],"json_path":path,"obj":v})
                        continue
                for k,val in v.items():
                    if isinstance(val,(dict,list)):stack.append((path+"."+str(k),val,depth+1))
            elif isinstance(v,list):
                for i,val in enumerate(v[:5000]):
                    if isinstance(val,(dict,list)):stack.append((path+f"[{i}]",val,depth+1))
    print("BPTERM",term,json.dumps(out[-50:],ensure_ascii=False)[:90000])
