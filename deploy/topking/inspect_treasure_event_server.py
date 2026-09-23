import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,page_text,assets_json,captured_at
                                        FROM treasure_guide_captures ORDER BY id""")]

qs=[r for r in rows if str(r["path"]).startswith("/quests")]
print("QUEST_ROWS",json.dumps([
  {"id":r["id"],"path":r["path"],"len":len(r["payload_json"] or ""),"head":str(r["payload_json"] or "")[:180],"tail":str(r["payload_json"] or "")[-180:]}
  for r in qs
],ensure_ascii=False))

# valid quest payloads: recursively print small objects that look like cooking/event-minigame quests
for r in qs:
    raw=str(r["payload_json"] or "")
    try: obj=json.loads(raw)
    except: continue
    hits=[]
    def walk(v,path="$",depth=0):
        if depth>18 or len(hits)>300:return
        if isinstance(v,dict):
            blob=json.dumps(v,ensure_ascii=False,separators=(",",":"))
            low=blob.lower()
            if len(blob)<=16000 and (
                "cooking" in low or
                "event_minigame" in low or
                "treasurehunt_energy" in low or
                "hamstercola" in low or
                "treasure_map" in low
            ):
                hits.append({"path":path,"obj":v})
                return
            for k,val in v.items():
                if isinstance(val,(dict,list)):walk(val,path+"."+str(k),depth+1)
        elif isinstance(v,list):
            for i,val in enumerate(v[:5000]):
                if isinstance(val,(dict,list)):walk(val,path+f"[{i}]",depth+1)
    walk(obj)
    print("QUEST_VALID",r["id"],json.dumps(hits,ensure_ascii=False)[:100000])

# DOM snapshots + asset lists for quest page, to correlate item icons with text/screens.
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    if "Ежедневная готовка I" not in text:
        continue
    try: assets=json.loads(r.get("assets_json") or "[]")
    except: assets=[]
    item_assets=[a for a in assets if "/items/" in str(a)]
    print("QUEST_DOM",r["id"],json.dumps({"text":text[:6000],"assets":item_assets[:300]},ensure_ascii=False))
