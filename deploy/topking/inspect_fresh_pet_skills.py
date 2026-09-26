import importlib.util, json, re, time
from collections import defaultdict

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

now=int(time.time())
since=now-72*3600
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
        SELECT id,capture_key,player_id,source,path,payload_json,page_text,assets_json,captured_at
        FROM treasure_guide_captures
        WHERE captured_at>=?
        ORDER BY id DESC
        LIMIT 1200
    """,(since,))]

skill_terms=[
    "pet_skill","minigame_pet_skill_","mf_fair_pet_skill_",
    "more_money","more_food","fight_hp_up","fight_treasure_goblin",
    "fishing_map_finder","chest_finder","chest_map_finder","map_generator",
    "trader_maps","trader_keys","trader_rep"
]
ru_terms=[
    "Любитель покушать","Охотник за сокровищами","Любитель блестяшек","Боевая кладка",
    "Ключник","Картограф","Карты на прилавке","Рыбацкое чутьё","Любимчик торговцев",
    "Чутьё на сундуки","питом","навык"
]

def compact(value, limit=12000):
    try:
        text=json.dumps(value,ensure_ascii=False,separators=(",",":"))
    except Exception:
        text=str(value)
    return text[:limit]

def walk(value,path="$",depth=0):
    if depth>16:
        return
    yield path,value
    if isinstance(value,dict):
        for k,v in value.items():
            yield from walk(v,path+"."+str(k),depth+1)
    elif isinstance(value,list):
        for i,v in enumerate(value[:2500]):
            yield from walk(v,path+f"[{i}]",depth+1)

captures=[]
objects=[]
texts=[]
seen_obj=set()
for row in rows:
    payload_raw=str(row.get("payload_json") or "")
    page_text=re.sub(r"\s+"," ",str(row.get("page_text") or "")).strip()
    hay=(payload_raw+"\n"+page_text).lower()
    if not any(t.lower() in hay for t in skill_terms+ru_terms):
        continue
    captures.append({
        "id":row["id"],"capture_key":row["capture_key"],"player_id":row["player_id"],
        "source":row["source"],"path":row["path"],"captured_at":row["captured_at"],
        "payload_len":len(payload_raw),"page_text_len":len(page_text)
    })
    if page_text:
        low=page_text.lower()
        for term in ru_terms:
            pos=low.find(term.lower())
            if pos>=0:
                snippet=page_text[max(0,pos-500):pos+2200]
                key=(row["id"],snippet)
                if key not in seen_obj:
                    seen_obj.add(key)
                    texts.append({"capture":row["id"],"term":term,"snippet":snippet})
    if not payload_raw:
        continue
    try:
        obj=json.loads(payload_raw)
    except Exception:
        continue
    # Direct selective rows are the most useful and should be preserved whole.
    if isinstance(obj,dict) and isinstance(obj.get("rows"),list):
        for item in obj["rows"]:
            if not isinstance(item,dict):
                continue
            p=item.get("payload")
            blob=compact(item,20000)
            if any(t.lower() in blob.lower() for t in skill_terms+ru_terms):
                key=("row",row["id"],str(item.get("path")),compact(p,12000))
                if key in seen_obj: continue
                seen_obj.add(key)
                objects.append({
                    "capture":row["id"],"capture_path":row["path"],"row_path":item.get("path"),
                    "kind":"selective_row","value":item
                })
    # Also find smallest-ish dict/list nodes that contain skill markers.
    candidates=[]
    for jpath,val in walk(obj):
        if not isinstance(val,(dict,list)):
            continue
        blob=compact(val,50000)
        low=blob.lower()
        hits=[t for t in skill_terms if t.lower() in low]
        if not hits:
            continue
        candidates.append((len(blob),jpath,val,hits))
    candidates.sort(key=lambda x:x[0])
    for size,jpath,val,hits in candidates[:30]:
        key=("node",row["id"],jpath,compact(val,12000))
        if key in seen_obj: continue
        seen_obj.add(key)
        objects.append({
            "capture":row["id"],"capture_path":row["path"],"json_path":jpath,
            "kind":"json_node","hits":hits,"size":size,"value":val
        })

# Keep latest useful material but enough history to compare before/after rerolls.
result={
    "generated_at":now,
    "since":since,
    "capture_count":len(rows),
    "skill_capture_count":len(captures),
    "captures":captures[:140],
    "objects":objects[:320],
    "text_snippets":texts[:180]
}
print(json.dumps(result,ensure_ascii=False,indent=2))
# trigger: 2026-09-26T12:21+09:00\n