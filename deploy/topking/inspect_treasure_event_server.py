import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    row=db.execute("""SELECT id,payload_json FROM treasure_guide_captures
                      WHERE path='/shop/view' AND payload_json<>'' ORDER BY id ASC LIMIT 1""").fetchone()
raw=str(row["payload_json"] or "")
start=raw.find('"shop_lots":[')
lots=[]
if start>=0:
    i=raw.find('[',start)+1
    while i<len(raw):
        while i<len(raw) and raw[i] in " \r\n\t,": i+=1
        if i>=len(raw) or raw[i]!='{': break
        st=i; depth=0; ins=False; esc=False; j=i
        while j<len(raw):
            ch=raw[j]
            if ins:
                if esc: esc=False
                elif ch=='\\': esc=True
                elif ch=='"': ins=False
            else:
                if ch=='"': ins=True
                elif ch=='{': depth+=1
                elif ch=='}':
                    depth-=1
                    if depth==0:
                        try: lots.append(json.loads(raw[st:j+1]))
                        except: pass
                        i=j+1; break
            j+=1
        else: break
print("LOTS",len(lots))
ids=[]
for o in lots:
    oid=str(o.get("id") or "")
    if "r4" in oid.lower() and ("pet" in oid.lower() or "mission" in oid.lower() or "pm_" in oid.lower()):
        ids.append({
          "id":oid,
          "cost":o.get("cost"),
          "content":(o.get("lot_view") or {}).get("content_view"),
          "name":(o.get("lot_view") or {}).get("name"),
          "desc":(o.get("lot_view") or {}).get("desc")
        })
print("R4_ALL",json.dumps(ids,ensure_ascii=False))
