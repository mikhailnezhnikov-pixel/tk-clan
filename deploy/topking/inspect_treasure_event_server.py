import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    shop=db.execute("SELECT id,payload_json FROM treasure_guide_captures WHERE path='/shop/view' AND payload_json<>'' ORDER BY id ASC LIMIT 1").fetchone()
    buys=[dict(r) for r in db.execute("SELECT id,path,payload_json FROM treasure_guide_captures WHERE path IN ('/shop/buy','/fair/reroll') AND payload_json<>'' ORDER BY id DESC LIMIT 120")]

raw=str(shop["payload_json"] or "")
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
                if esc:esc=False
                elif ch=='\\':esc=True
                elif ch=='"':ins=False
            else:
                if ch=='"':ins=True
                elif ch=='{':depth+=1
                elif ch=='}':
                    depth-=1
                    if depth==0:
                        try:lots.append(json.loads(raw[st:j+1]))
                        except:pass
                        i=j+1;break
            j+=1
        else:break

targets=[
 "mf_fair_treasury_room_choose_way_1",
 "mf_fair_treasury_room_choose_way_2",
 "mf_fair_treasury_room_choose_way_3",
 "mf_treasurelot_chest_type_015",
 "mf_treasurelot_chest_type_02",
 "mf_treasurelot_chest_type_03",
 "mf_fairlot_minigame_treasury_room_big_chest",
 "mf_fairlot_minigame_fight_room_big_chest"
]
byid={str(x.get("id") or ""):x for x in lots}
for t in targets:
    o=byid.get(t)
    print("LOT",t,json.dumps(o,ensure_ascii=False) if o else "null")

# latest fair states for treasury/chests
states=[]
for r in buys:
    try:obj=json.loads(r["payload_json"])
    except:continue
    fairs=obj.get("fair") if isinstance(obj,dict) else None
    if not isinstance(fairs,list):continue
    for fair in fairs:
        if not isinstance(fair,dict):continue
        fid=str(fair.get("id") or "")
        if fid not in ("fair_treasury_room","fair_mini_game_chests"):continue
        states.append({
          "capture":r["id"],
          "fair":fid,
          "reroll_cost":fair.get("fair_reroll_cost"),
          "slots":[
            {"id":s.get("id"),"lot":s.get("shop_lot_id"),"bought":s.get("is_bought")}
            for s in (fair.get("fair_slots") or []) if isinstance(s,dict)
          ]
        })
print("STATES",json.dumps(states[:20],ensure_ascii=False))
