import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,page_text,captured_at
                                        FROM treasure_guide_captures ORDER BY id""")]

shop=next((str(r["payload_json"] or "") for r in rows if r["path"]=="/shop/view"),"")
start=shop.find('"shop_lots":[')
start=shop.find('[',start)+1 if start>=0 else -1
objs=[]
if start>=0:
    i=start;n=len(shop)
    while i<n:
        while i<n and shop[i] in ' \r\n\t,': i+=1
        if i>=n or shop[i]!='{': break
        depth=0;ins=False;esc=False;j=i
        while j<n:
            ch=shop[j]
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
                        try: objs.append(json.loads(shop[i:j+1]))
                        except: pass
                        i=j+1;break
            j+=1
        else: break
        if depth!=0: break

pat=re.compile(r"(treasury_room|treasurelot_|fair_pet_skill|fair_lab_slot_pet|pm_|minigame_(?:trader|fishing|fight|chests|lights))",re.I)
dynamic=[]
for o in objs:
    oid=str(o.get("id") or "")
    if not pat.search(oid) or "achievement" in oid: continue
    view=o.get("lot_view") if isinstance(o.get("lot_view"),dict) else {}
    dynamic.append({
      "id":oid,
      "cost":o.get("cost"),
      "content_view":view.get("content_view"),
      "name":view.get("name"),
      "desc":view.get("desc"),
      "icon":view.get("icon_card"),
      "is_ad":o.get("is_ad"),
      "priority":o.get("priority")
    })
print("DYNAMIC_COUNT",len(dynamic))
print("DYNAMIC_LOTS",json.dumps(dynamic,ensure_ascii=False))

# Active DOM snapshots for minigame screens. Deduplicate exact normalized text.
keywords=["Сокровищница","Рыбалка","Торговец","Сундук","Сундуки","Сражение","Лабиринт","Загадка","Питомцы","Поручения питомцам"]
for kw in keywords:
    seen=set(); vals=[]
    for r in rows:
        text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
        if kw.lower() not in text.lower(): continue
        if text in seen: continue
        seen.add(text)
        # Keep only snapshots likely focused on this screen, not giant achievement list.
        if len(text)>9000: continue
        vals.append({"id":r["id"],"len":len(text),"text":text[:5000]})
    print("DOM",kw,json.dumps(vals[-12:],ensure_ascii=False))
