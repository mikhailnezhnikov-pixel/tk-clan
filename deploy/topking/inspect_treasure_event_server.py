import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    row=db.execute("""SELECT id,payload_json FROM treasure_guide_captures
                      WHERE path='/shop/view' AND payload_json<>'' ORDER BY id DESC LIMIT 1""").fetchone()
raw=str(row["payload_json"] or "")
print("SHOP_CAPTURE",row["id"],len(raw))

start=raw.find('"shop_lots":[')
if start<0: raise SystemExit("shop_lots missing")
i=raw.find('[',start)+1
lots=[]
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

skills=[]
missions=[]
for o in lots:
    oid=str(o.get("id") or "")
    if oid.startswith("mf_fair_pet_skill_"):
        skills.append(o)
    if oid.startswith("mf_pm_") and re.search(r"_r[1-4]_(?:x\d+|done)$",oid):
        missions.append(o)

print("SKILL_LOTS",json.dumps(skills,ensure_ascii=False,separators=(",",":")))
# representative one per rank and exact r4
rep=[]
seen=set()
for o in missions:
    m=re.search(r"_r([1-4])_",o.get("id",""))
    rank=m.group(1) if m else "?"
    if rank not in seen or rank=="4":
        seen.add(rank);rep.append(o)
print("MISSION_LOTS",json.dumps(rep[:80],ensure_ascii=False,separators=(",",":")))
