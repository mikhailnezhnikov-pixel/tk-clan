import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,page_text FROM treasure_guide_captures ORDER BY id""")]

# Parse full shop catalog.
shop_row=next((r for r in rows if r["path"]=="/shop/view" and r["payload_json"]),None)
lots=[]
if shop_row:
    raw=str(shop_row["payload_json"])
    start=raw.find('"shop_lots":[')
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

out=[]
for o in lots:
    oid=str(o.get("id") or "")
    low=oid.lower()
    if "achievement" in low: continue
    if not re.search(r"trader|chest|treasury|treasurelot|map4coins",low): continue
    out.append({
      "id":oid,
      "cost":o.get("cost"),
      "content":(o.get("lot_view") or {}).get("content_view"),
      "name":(o.get("lot_view") or {}).get("name"),
      "desc":(o.get("lot_view") or {}).get("desc"),
      "qty":(o.get("lot_view") or {}).get("quantity"),
      "icon":(o.get("lot_view") or {}).get("icon_card")
    })
print("CATALOG",json.dumps(out,ensure_ascii=False))

# All fair states ever captured: trader/chests/treasury slots.
states=[]
for r in rows:
    try: obj=json.loads(r.get("payload_json") or "")
    except: continue
    fairs=obj.get("fair") if isinstance(obj,dict) else None
    if not isinstance(fairs,list): continue
    for fair in fairs:
        if not isinstance(fair,dict): continue
        fid=str(fair.get("id") or "")
        if not re.search(r"trader|chest|treasury",fid,re.I): continue
        slots=[{"slot":s.get("id"),"lot":s.get("shop_lot_id"),"bought":s.get("is_bought")}
               for s in (fair.get("fair_slots") or []) if isinstance(s,dict)]
        states.append({"capture":r["id"],"path":r["path"],"fair":fid,"slots":slots})
print("STATES",json.dumps(states[-120:],ensure_ascii=False))

# DOM screens from all history for trader/chest/quest.
for label,pattern in [
  ("TRADER",r"Тайный Торговец"),
  ("CHEST",r"Охота за сундуками|Сундук сокровищницы"),
  ("QUEST",r"Ежедневная готовка|Карты на каждый день|Задания Сокровищ")
]:
    vals=[]
    seen=set()
    rx=re.compile(pattern,re.I)
    for r in rows:
        text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
        if not text or not rx.search(text): continue
        key=text[:1400]
        if key in seen: continue
        seen.add(key)
        vals.append({"id":r["id"],"text":text[:5000]})
    print("ALL_"+label,json.dumps(vals[-120:],ensure_ascii=False))
