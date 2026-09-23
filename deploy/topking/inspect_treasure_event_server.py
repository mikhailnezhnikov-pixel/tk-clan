import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    row=db.execute("""SELECT payload_json FROM treasure_guide_captures
                      WHERE path='/shop/view' ORDER BY id DESC LIMIT 1""").fetchone()
shop=str(row[0] or "") if row else ""

start=shop.find('"shop_lots":[')
if start<0:
    print("NO_SHOP_LOTS"); raise SystemExit
start=shop.find('[',start)+1

objs=[]
i=start
n=len(shop)
while i<n:
    while i<n and shop[i] in ' \r\n\t,': i+=1
    if i>=n or shop[i]!= '{': break
    depth=0; in_str=False; esc=False; j=i
    while j<n:
        ch=shop[j]
        if in_str:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch=='"': in_str=False
        else:
            if ch=='"': in_str=True
            elif ch=='{': depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:
                    raw=shop[i:j+1]
                    try: objs.append(json.loads(raw))
                    except Exception as e: print("OBJ_PARSE_ERROR",len(objs),repr(e))
                    i=j+1
                    break
        j+=1
    else:
        break
    if depth!=0: break

print("SHOP_OBJECTS_PARSED",len(objs))
ids=[str(o.get("id") or "") for o in objs]
print("FIRST_IDS",json.dumps(ids[:20],ensure_ascii=False))
print("LAST_IDS",json.dumps(ids[-20:],ensure_ascii=False))

patterns={
  "treasury": re.compile(r"treasury_room|treasure.*treasury",re.I),
  "chests": re.compile(r"treasurelot_chest|minigame_chests",re.I),
  "trader": re.compile(r"treasurelot_trader|minigame_trader",re.I),
  "pet_skills": re.compile(r"fair_pet_skill",re.I),
  "fishing": re.compile(r"treasurelot_fishing|is_fishing|fishing_rod",re.I),
  "fight": re.compile(r"treasurelot_(?:sword|enemy)|minigame_fight",re.I),
  "lights": re.compile(r"lights_out|minigame_lights",re.I),
  "maps": re.compile(r"treasurelot_map_|event_treasure_map",re.I),
  "shop_event": re.compile(r"treasure_offer|treasurehunt|event_treasure",re.I),
}
for label,pat in patterns.items():
    selected=[]
    for o in objs:
        oid=str(o.get("id") or "")
        if not pat.search(oid): continue
        view=o.get("lot_view") if isinstance(o.get("lot_view"),dict) else {}
        selected.append({
          "id":oid,
          "cost":o.get("cost"),
          "content_view":view.get("content_view"),
          "name":view.get("name"),
          "desc":view.get("desc"),
          "icon":view.get("icon_card"),
          "meta":o.get("meta"),
          "priority":o.get("priority"),
          "is_ad":o.get("is_ad")
        })
    print("CATEGORY",label,"COUNT",len(selected))
    print("CATEGORY_DATA",label,json.dumps(selected,ensure_ascii=False)[:60000])
