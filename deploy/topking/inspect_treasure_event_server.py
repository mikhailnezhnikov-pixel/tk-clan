import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    row=db.execute("SELECT id,payload_json FROM treasure_guide_captures WHERE path='/shop/buy' AND payload_json<>'' ORDER BY id DESC LIMIT 1").fetchone()

raw=str(row["payload_json"] or "")
print("CAPTURE",row["id"],"LEN",len(raw))
for key in ['"shop_lots":[','"fairs":[','"items":[']:
    print("KEY",key,raw.find(key))

start=raw.find('"shop_lots":[')
lots=[]
if start>=0:
    i=raw.find('[',start)+1
    while i<len(raw):
        while i<len(raw) and raw[i] in " \r\n\t,": i+=1
        if i>=len(raw) or raw[i]!='{': break
        st=i;depth=0;ins=False;esc=False;j=i
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
                        i=j+1;break
            j+=1
        else: break

pet=[o for o in lots if str(o.get("id") or "").startswith("mf_pm_") or str(o.get("id") or "").startswith("mf_fair_pet_skill_")]
print("PARSED",len(lots),"PET",len(pet))
print("PETLOTS",json.dumps(pet,ensure_ascii=False,separators=(",",":"))[:120000])
