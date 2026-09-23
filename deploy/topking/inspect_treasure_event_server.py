import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("SELECT id,path,payload_json,page_text,captured_at FROM treasure_guide_captures ORDER BY id")]

# Parse complete shop lots.
shop=next((str(r["payload_json"] or "") for r in rows if r["path"]=="/shop/view"),"")
start=shop.find('"shop_lots":['); start=shop.find('[',start)+1 if start>=0 else -1
objs=[]
if start>=0:
    i=start;n=len(shop)
    while i<n:
        while i<n and shop[i] in ' \r\n\t,': i+=1
        if i>=n or shop[i]!='{': break
        d=0;ins=False;esc=False;j=i
        while j<n:
            ch=shop[j]
            if ins:
                if esc: esc=False
                elif ch=='\\': esc=True
                elif ch=='"': ins=False
            else:
                if ch=='"': ins=True
                elif ch=='{': d+=1
                elif ch=='}':
                    d-=1
                    if d==0:
                        try: objs.append(json.loads(shop[i:j+1]))
                        except: pass
                        i=j+1;break
            j+=1
        else: break
        if d!=0: break

def compact(o):
    v=o.get("lot_view") if isinstance(o.get("lot_view"),dict) else {}
    return {"id":o.get("id"),"cost":o.get("cost"),"rewards":v.get("content_view"),"name":v.get("name"),"desc":v.get("desc"),"icon":v.get("icon_card"),"ad":o.get("is_ad")}

mission=[compact(o) for o in objs if re.match(r"mf_pm_(?:fish|mothcat)_",str(o.get("id") or ""))]
print("PET_MISSION_LOTS",json.dumps(mission,ensure_ascii=False))

# All compact modal texts the user opened, excluding the general achievement list.
modals=[];seen=set()
for r in rows:
    t=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    if "Понятно" not in t or len(t)>1800: continue
    pos=t.rfind(" HK ")
    body=t[pos+4:] if pos>=0 else t
    if len(body)>500 or body in seen: continue
    seen.add(body)
    modals.append({"id":r["id"],"body":body})
print("ALL_MODALS",json.dumps(modals,ensure_ascii=False))
