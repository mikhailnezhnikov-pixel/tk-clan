import importlib.util, json, re

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

TERMS=[
  "more_money","more_food","fight_hp_up","fight_treasure_goblin",
  "fishing_map_finder","chest_finder","chest_map_finder","map_generator",
  "trader_maps","trader_keys","trader_rep"
]

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
      SELECT id,path,payload_json,page_text,captured_at
      FROM treasure_guide_captures
      WHERE payload_json<>'' OR page_text<>''
      ORDER BY id
    """)]

def dump(v):
    try:
        return json.dumps(v,ensure_ascii=False,separators=(",",":"))
    except Exception:
        return ""

def walk(v,path="$",parent=None,parent_path=None,depth=0):
    if depth>20:
        return
    yield path,v,parent,parent_path
    if isinstance(v,dict):
        for k,val in v.items():
            yield from walk(val,path+"."+str(k),v,path,depth+1)
    elif isinstance(v,list):
        for i,val in enumerate(v[:6000]):
            yield from walk(val,path+f"[{i}]",v,path,depth+1)

for term in TERMS:
    hits=[]
    for row in rows:
        raw=row.get("payload_json") or ""
        if term.lower() not in raw.lower():
            continue
        try:
            obj=json.loads(raw)
        except Exception:
            continue

        seen=set()
        for path,val,parent,parent_path in walk(obj):
            if isinstance(val,str) and term.lower() in val.lower():
                candidates=[]
                if isinstance(parent,dict):
                    candidates.append((parent_path,parent))
                # one more parent level by resolving prefix from root
                if parent_path:
                    prefix=parent_path.rsplit(".",1)[0] if "." in parent_path else "$"
                    # resolve only simple dot/list path by scanning all containers and matching exact path
                    for p2,v2,_,__ in walk(obj):
                        if p2==prefix and isinstance(v2,(dict,list)):
                            candidates.append((p2,v2))
                            break
                for cpath,cval in candidates:
                    blob=dump(cval)
                    key=(row["id"],cpath,blob[:500])
                    if key in seen or len(blob)>18000:
                        continue
                    seen.add(key)
                    hits.append({
                      "capture":row["id"],
                      "capture_path":row["path"],
                      "json_path":cpath,
                      "value":cval
                    })
    print("SKILL_PARENT",term,json.dumps(hits[-30:],ensure_ascii=False)[:120000])

# Also print exact current fair skill slots / bought responses with all sibling fields.
slot_hits=[]
for row in rows:
    raw=row.get("payload_json") or ""
    if "mf_fair_pet_skill_" not in raw:
        continue
    try:
        obj=json.loads(raw)
    except Exception:
        continue
    for path,val,_,__ in walk(obj):
        if isinstance(val,dict):
            blob=dump(val)
            if "mf_fair_pet_skill_" in blob and len(blob)<=12000:
                if any(k in val for k in ("shop_lot_id","id","cost","costs","lot_view","meta","content_view","rewards","reward")):
                    slot_hits.append({
                      "capture":row["id"],
                      "capture_path":row["path"],
                      "json_path":path,
                      "value":val
                    })
print("SKILL_SLOT_OBJECTS",json.dumps(slot_hits[-120:],ensure_ascii=False)[:180000])

# Compact DOM snippets mentioning pet skill/level wording.
dom=[]
for row in rows:
    text=re.sub(r"\s+"," ",str(row.get("page_text") or "")).strip()
    low=text.lower()
    if not text:
        continue
    if ("навык" in low or "skill" in low) and ("питом" in low or "pet" in low):
        dom.append({"capture":row["id"],"path":row["path"],"text":text[-3500:]})
print("SKILL_DOM",json.dumps(dom[-80:],ensure_ascii=False)[:120000])
