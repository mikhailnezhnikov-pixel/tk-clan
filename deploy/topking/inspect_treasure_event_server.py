import importlib.util,json,re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json FROM treasure_guide_captures
                                        WHERE path='/shop/view' AND payload_json<>'' ORDER BY id""")]

for r in rows[:6]:
    raw=str(r["payload_json"] or "")
    start=raw.find('"shop_lots":[')
    if start<0: continue
    lots=[]
    i=raw.find('[',start)+1
    while i<len(raw):
        while i<len(raw) and raw[i] in " \r\n\t,": i+=1
        if i>=len(raw) or raw[i]!='{': break
        st=i;depth=0;ins=False;esc=False;j=i
        while j<len(raw):
            ch=raw[j]
            if ins:
                if esc:esc=False
                elif ch=='\\':esc=True
                elif ch=='"':ins=False
            else:
                if ch=='"':ins=True
                elif ch=='{':depth+=1
                elif ch=='}':
                    depth-=1
                    if depth==0:
                        try:lots.append(json.loads(raw[st:j+1]))
                        except:pass
                        i=j+1;break
            j+=1
        else:break
    out=[]
    for o in lots:
        oid=str(o.get("id") or "")
        if re.search(r"forest|mine",oid,re.I):
            out.append(o)
    if out:
        print("ROOM_LOTS",r["id"],json.dumps(out,ensure_ascii=False))
        break
