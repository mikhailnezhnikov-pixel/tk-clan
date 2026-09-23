import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,page_text,assets_json
                                        FROM treasure_guide_captures ORDER BY id""")]

# Parse relevant shop lots from the most recent /shop/view capture.
shop_row=next((r for r in reversed(rows) if r["path"]=="/shop/view" and r["payload_json"]),None)
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

want=lambda o: re.search(r"^mf_shoplot_treasure_|big_chest$|treasury_room_choose_way_|achievement_(?:01|02)_",str(o.get("id") or ""),re.I)
summ=[]
for o in lots:
    if not want(o): continue
    summ.append({
      "id":o.get("id"),
      "cost":o.get("cost"),
      "content":(o.get("lot_view") or {}).get("content_view"),
      "quantity":(o.get("lot_view") or {}).get("quantity"),
      "name":(o.get("lot_view") or {}).get("name"),
      "desc":(o.get("lot_view") or {}).get("desc"),
      "icon":(o.get("lot_view") or {}).get("icon_card")
    })
print("EXACT_LOTS",json.dumps(summ,ensure_ascii=False))

# DOM text fragments related to pet skill/property popups and rewards.
patterns=[
  r"ключ",r"корм",r"монет",r"HP",r"здоров",r"ягод",r"питомц",r"навык",
  r"торгов",r"гоблин",r"рыбк",r"сокровищ",r"урон",r"шанс"
]
for pat in patterns:
    hits=[]
    rx=re.compile(pat,re.I)
    for r in rows:
        text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
        if not text or not rx.search(text): continue
        # capture local windows around first two matches
        for m in list(rx.finditer(text))[:2]:
            hits.append({"id":r["id"],"snippet":text[max(0,m.start()-350):m.end()+900]})
    print("DOM_TERM",pat,json.dumps(hits[:20],ensure_ascii=False))
