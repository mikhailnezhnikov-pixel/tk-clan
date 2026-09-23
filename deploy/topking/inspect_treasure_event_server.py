import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,path,payload_json,page_text
                                        FROM treasure_guide_captures ORDER BY id""")]

# Search all quest payloads/selective rows for cooking/treasure quest objects.
terms=["cooking","treasure","event_minigame","quest"]
matches=[]
for r in rows:
    if not str(r["path"]).startswith("/quests"):
        continue
    raw=str(r.get("payload_json") or "")
    if not raw: continue
    try:
        obj=json.loads(raw)
    except:
        continue
    def walk(v,path="$",depth=0):
        if depth>16 or len(matches)>300: return
        if isinstance(v,dict):
            try: blob=json.dumps(v,ensure_ascii=False,separators=(",",":"))
            except: blob=""
            low=blob.lower()
            if len(blob)<=12000 and ("cooking" in low or "treasure" in low or "minigame" in low):
                matches.append({"capture":r["id"],"capture_path":r["path"],"json_path":path,"obj":v})
                return
            for k,val in v.items():
                if isinstance(val,(dict,list)): walk(val,path+"."+str(k),depth+1)
        elif isinstance(v,list):
            for i,val in enumerate(v[:3000]):
                if isinstance(val,(dict,list)): walk(val,path+f"[{i}]",depth+1)
    walk(obj)

print("QUEST_OBJECTS",json.dumps(matches,ensure_ascii=False)[:120000])

# Trader DOM modals with exact visible names and prices.
mods=[]
seen=set()
for r in rows:
    text=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    if "Тайный Торговец" not in text: continue
    if "СОДЕРЖИТ" not in text and "Понятно" not in text: continue
    pos=text.rfind(" HK ")
    tail=(text[pos+4:] if pos>=0 else text)[:3000]
    if tail in seen: continue
    seen.add(tail)
    mods.append({"id":r["id"],"text":tail})
print("TRADER_MODALS",json.dumps(mods,ensure_ascii=False))
