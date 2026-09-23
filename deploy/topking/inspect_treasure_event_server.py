import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,page_text,captured_at
                                        FROM treasure_guide_captures ORDER BY id""")]

# Parse complete shop_lots from truncated /shop/view.
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
                        i=j+1; break
            j+=1
        else: break
        if d!=0: break

def compact(o):
    v=o.get("lot_view") if isinstance(o.get("lot_view"),dict) else {}
    return {"id":o.get("id"),"cost":o.get("cost"),"rewards":v.get("content_view"),"name":v.get("name"),"desc":v.get("desc"),"icon":v.get("icon_card"),"ad":o.get("is_ad")}

cats={
 "treasury":[r"treasury_room_choose_way",r"treasury_room_big_chest"],
 "trader":[r"treasurelot_trader",r"fairlot_minigame_trader_(?!achievement)"],
 "pet_skill":[r"fair_pet_skill"],
 "fishing":[r"treasurelot_fishing",r"treasurelot_is_fishing"],
 "fight":[r"treasurelot_sword",r"treasurelot_enemy"],
 "chests":[r"treasurelot_chest_type",r"treasurelot_chest_digging",r"treasurelot_chest_empty"],
 "lights":[r"fairlot_lights_out_sl"],
}
for label,patterns in cats.items():
    arr=[]
    for o in objs:
        oid=str(o.get("id") or "")
        if "achievement" in oid: continue
        if any(re.search(p,oid,re.I) for p in patterns): arr.append(compact(o))
    print("LOT_CAT",label,json.dumps(arr,ensure_ascii=False))

# Focused modal/page snapshots: only compact (<1800 chars), remove common nav prefix.
for label,needles in {
  "treasury":["Сокровищница","МОЖНО ОТЫСКАТЬ"],
  "trader":["Торговец","МОЖНО ОТЫСКАТЬ"],
  "chests":["Сундук","МОЖНО ОТЫСКАТЬ"],
  "fishing":["Рыбалка","МОЖНО ОТЫСКАТЬ"],
  "fight":["Сражение","МОЖНО ОТЫСКАТЬ"],
  "lights":["Лабиринт","Понятно"],
  "pets":["Рыбка","Понятно"]
}.items():
    vals=[]; seen=set()
    for r in rows:
        text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
        if len(text)>1800: continue
        if not all(n.lower() in text.lower() for n in needles): continue
        pos=text.rfind(" HK ")
        body=text[pos+4:] if pos>=0 else text
        if body in seen: continue
        seen.add(body)
        vals.append({"id":r["id"],"body":body[:1200]})
    print("MODAL",label,json.dumps(vals[-20:],ensure_ascii=False))
