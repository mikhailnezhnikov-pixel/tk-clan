import importlib.util, json, re
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

terms=[
 "fight_hp_up","more_food","more_money","chest_finder","fishing_map_finder",
 "trader_rep","trader_keys","treasure_goblin","map_generator","trader_maps"
]
with server.db_session() as db:
    for term in terms:
        rows=[dict(r) for r in db.execute("""
          SELECT id,path,payload_json,page_text,captured_at
          FROM treasure_guide_captures
          WHERE (path LIKE '/localization/%' OR path LIKE '%localization%')
            AND (payload_json LIKE ? OR page_text LIKE ?)
          ORDER BY id DESC LIMIT 30
        """,("%"+term+"%","%"+term+"%"))]
        print("TERM",term,"LOC_COUNT",len(rows))
        for r in rows:
            raw=str(r.get("payload_json") or "")
            txt=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
            for source_name,source in (("JSON",raw),("TEXT",txt)):
                low=source.lower()
                pos=low.find(term.lower())
                if pos>=0:
                    print("LOC",term,r["id"],r["captured_at"],r["path"],source_name,
                          source[max(0,pos-2500):pos+9000].replace("\n"," ")[:11500])
                    break

# Search all captured payloads for likely human-readable strings adjacent to fight_hp_up,
# but skip giant player/fair state blobs dominated by counters.
with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""
      SELECT id,path,payload_json,page_text,captured_at
      FROM treasure_guide_captures
      WHERE (payload_json LIKE '%fight_hp_up%' OR page_text LIKE '%fight_hp_up%')
      ORDER BY id DESC LIMIT 250
    """)]
print("FIGHT_ROWS",len(rows))
for r in rows:
    raw=str(r.get("payload_json") or "")
    if len(raw)>80000 and r["path"].startswith("/fair/"): continue
    pos=raw.lower().find("fight_hp_up")
    if pos>=0:
        print("FIGHT",r["id"],r["captured_at"],r["path"],raw[max(0,pos-3000):pos+10000].replace("\n"," ")[:13000])
