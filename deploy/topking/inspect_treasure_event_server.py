import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("SELECT id,path,payload_json,page_text FROM treasure_guide_captures ORDER BY id")]

# full shop catalog
shop_row=next((r for r in rows if r["path"]=="/shop/view" and r["payload_json"]),None)
lots=[]
raw=str(shop_row["payload_json"] or "") if shop_row else ""
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
byid={str(o.get("id") or ""):o for o in lots}

observed={"trader":set(),"chests":set()}
for r in rows:
    try: obj=json.loads(r.get("payload_json") or "")
    except: continue
    fairs=obj.get("fair") if isinstance(obj,dict) else None
    if not isinstance(fairs,list): continue
    for fair in fairs:
        if not isinstance(fair,dict): continue
        fid=str(fair.get("id") or "")
        target="trader" if fid=="fair_mini_game_trader" else ("chests" if fid=="fair_mini_game_chests" else None)
        if not target: continue
        for s in fair.get("fair_slots") or []:
            if isinstance(s,dict) and s.get("shop_lot_id"):
                lot=str(s["shop_lot_id"])
                if lot not in ("mf_fairlot_empty","mf_fair_pet_skill_locked_by_bonus"):
                    observed[target].add(lot)

for group in ("trader","chests"):
    out=[]
    for oid in sorted(observed[group]):
        o=byid.get(oid)
        if o:
            lv=o.get("lot_view") or {}
            out.append({"id":oid,"cost":o.get("cost"),"content":lv.get("content_view"),"name":lv.get("name"),"desc":lv.get("desc"),"icon":lv.get("icon_card")})
        else:
            out.append({"id":oid,"missing_definition":True})
    print(group.upper()+"_DEFS",json.dumps(out,ensure_ascii=False))

# compact quest modal text only
q=[]
seen=set()
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    if not text: continue
    if not ("Ежедневная готовка" in text or "Карты на каждый день" in text or "Коллекция" in text): continue
    # keep modal tail if possible
    pos=text.rfind(" HK ")
    tail=text[pos+4:] if pos>=0 else text
    tail=tail[:2600]
    if tail in seen: continue
    seen.add(tail); q.append({"id":r["id"],"text":tail})
print("QUEST_DETAILS",json.dumps(q,ensure_ascii=False))
