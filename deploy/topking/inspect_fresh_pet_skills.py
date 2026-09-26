import importlib.util, json, re, time

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

now=int(time.time())
since=now-24*3600
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
        SELECT id,capture_key,player_id,source,path,payload_json,page_text,captured_at
        FROM treasure_guide_captures
        WHERE captured_at>=?
        ORDER BY id DESC
        LIMIT 500
    """,(since,))]

needles=[
 "pet_skill","minigame_pet_skill_","mf_fair_pet_skill_",
 "more_money","more_food","fight_hp_up","fight_treasure_goblin","fight_egg_spawn",
 "fishing_map_finder","chest_finder","chest_map_finder","map_generator",
 "trader_maps","trader_keys","trader_rep"
]
ru=[
 "Любитель покушать","Охотник за сокровищами","Любитель блестяшек","Боевая кладка",
 "Ключник","Картограф","Карты на прилавке","Рыбацкое чутьё","Любимчик торговцев",
 "Чутьё на сундуки","питом","навык"
]

captures=[]
selective=[]
raw_hits=[]
texts=[]
for row in rows:
    raw=str(row.get("payload_json") or "")
    text=re.sub(r"\s+"," ",str(row.get("page_text") or "")).strip()
    low=(raw+"\n"+text).lower()
    hit_terms=[x for x in needles if x.lower() in low]
    hit_ru=[x for x in ru if x.lower() in low]
    if not hit_terms and not hit_ru:
        continue
    captures.append({
      "id":row["id"],"capture_key":row["capture_key"],"player_id":row["player_id"],
      "source":row["source"],"path":row["path"],"captured_at":row["captured_at"],
      "terms":hit_terms,"ru_terms":hit_ru,"payload_len":len(raw),"page_text_len":len(text)
    })

    # Preserve direct selective rows from live APIs.
    if raw:
        try: obj=json.loads(raw)
        except Exception: obj=None
        if isinstance(obj,dict) and isinstance(obj.get("rows"),list):
            for item in obj["rows"]:
                if not isinstance(item,dict): continue
                blob=json.dumps(item,ensure_ascii=False,separators=(",",":"))
                if any(x.lower() in blob.lower() for x in needles+ru):
                    selective.append({
                      "capture":row["id"],"capture_path":row["path"],
                      "captured_at":row["captured_at"],"row":item
                    })

        # Cheap raw snippets around exact ids catch catalog/localization captures.
        raw_low=raw.lower()
        for term in needles:
            start=0
            count=0
            while count<6:
                pos=raw_low.find(term.lower(),start)
                if pos<0: break
                raw_hits.append({
                  "capture":row["id"],"capture_path":row["path"],"captured_at":row["captured_at"],
                  "term":term,"snippet":raw[max(0,pos-1000):pos+5000]
                })
                start=pos+len(term); count+=1

    if text:
        txt_low=text.lower()
        for term in ru:
            pos=txt_low.find(term.lower())
            if pos>=0:
                texts.append({
                  "capture":row["id"],"capture_path":row["path"],"captured_at":row["captured_at"],
                  "term":term,"snippet":text[max(0,pos-600):pos+2600]
                })

# newest first in DB query; keep enough history to compare rerolls.
result={
 "generated_at":now,"since":since,"capture_count":len(rows),
 "skill_capture_count":len(captures),
 "captures":captures[:160],
 "selective_rows":selective[:400],
 "raw_hits":raw_hits[:260],
 "text_snippets":texts[:160]
}
print(json.dumps(result,ensure_ascii=False,indent=2))
# trigger: optimized 2026-09-26T12:23+09:00
