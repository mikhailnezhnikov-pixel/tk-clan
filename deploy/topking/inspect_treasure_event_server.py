import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,source,path,payload_json,page_text,captured_at
                                        FROM treasure_guide_captures ORDER BY id""")]

print("MAX_ID", rows[-1]["id"] if rows else 0)
fresh=[r for r in rows if r["id"]>=1184]
print("FRESH_COUNT",len(fresh))
print("FRESH_PATHS",json.dumps({p:sum(1 for r in fresh if r["path"]==p) for p in sorted(set(r["path"] for r in fresh))},ensure_ascii=False))

def norm(s):
    return re.sub(r"\s+"," ",str(s or "")).strip()

# Fresh DOM screens: quests, trader, chests, purchase/reward modals.
groups={"QUEST":[],"TRADER":[],"CHEST":[],"MODAL":[]}
seen={k:set() for k in groups}
for r in fresh:
    text=norm(r.get("page_text"))
    if not text:
        continue
    targets=[]
    if "Задания" in text and ("Ежедневная готовка" in text or "Карты на каждый день" in text or "Задания Сокровищ" in text):
        targets.append("QUEST")
    if "Тайный Торговец" in text:
        targets.append("TRADER")
    if "Охота за сундуками" in text or "Сундук сокровищницы" in text:
        targets.append("CHEST")
    if "СОДЕРЖИТ" in text or "МОЖНО ОТЫСКАТЬ" in text or "МОЖНО НАЙТИ" in text:
        targets.append("MODAL")
    for g in targets:
        key=text[:1200]
        if key in seen[g]: continue
        seen[g].add(key)
        groups[g].append({"id":r["id"],"path":r["path"],"text":text[:5000]})

for g,vals in groups.items():
    print("DOM_"+g,json.dumps(vals[-80:],ensure_ascii=False))

# Parse first full /shop/view shop_lots for exact relevant definitions.
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

rel=[]
for o in lots:
    oid=str(o.get("id") or "")
    if re.search(r"minigame_(?:trader|chests)|treasurelot_(?:chest|trader)|quest|treasure_",oid,re.I):
        rel.append({
          "id":oid,
          "cost":o.get("cost"),
          "content":(o.get("lot_view") or {}).get("content_view"),
          "name":(o.get("lot_view") or {}).get("name"),
          "desc":(o.get("lot_view") or {}).get("desc"),
          "qty":(o.get("lot_view") or {}).get("quantity"),
          "icon":(o.get("lot_view") or {}).get("icon_card")
        })
print("RELEVANT_LOTS",json.dumps(rel,ensure_ascii=False))

# Fresh fair/shop responses: relevant slot ids and buy-state.
state=[]
for r in fresh:
    if r["path"] not in ("/shop/buy","/fair/reroll"):
        continue
    try: obj=json.loads(r["payload_json"] or "")
    except: continue
    fairs=obj.get("fair")
    if not isinstance(fairs,list): continue
    for fair in fairs:
        if not isinstance(fair,dict): continue
        fid=str(fair.get("id") or "")
        if fid not in ("fair_mini_game_trader","fair_mini_game_chests","fair_quest","fair_treasures") and "trader" not in fid and "chest" not in fid and "quest" not in fid:
            continue
        slots=[]
        for s in fair.get("fair_slots") or []:
            if isinstance(s,dict):
                slots.append({"slot":s.get("id"),"lot":s.get("shop_lot_id"),"bought":s.get("is_bought")})
        state.append({"capture":r["id"],"fair":fid,"slots":slots})
print("FRESH_FAIRS",json.dumps(state[-80:],ensure_ascii=False))
