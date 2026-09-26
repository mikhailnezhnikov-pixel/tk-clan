import importlib.util, json, re, time
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

targets=[
 "mf_fair_pet_skill_fight_hp_up_r4",
 "mf_fair_pet_skill_more_food_r1",
 "mf_fair_pet_skill_more_money_r3",
 "mf_fair_pet_skill_chest_finder_r1",
 "mf_fair_pet_skill_chest_finder_r4",
 "mf_fair_pet_skill_trader_keys_r3",
 "mf_fair_pet_skill_treasure_goblin_r4",
]
with server.db_session() as db:
    for target in targets:
        rows=[dict(r) for r in db.execute("""
          SELECT id,path,payload_json,page_text,captured_at
          FROM treasure_guide_captures
          WHERE payload_json LIKE ?
          ORDER BY id DESC LIMIT 12
        """,("%"+target+"%",))]
        print("TARGET",target,"COUNT",len(rows))
        for r in rows:
            raw=str(r.get("payload_json") or "")
            positions=[m.start() for m in re.finditer(re.escape(target),raw)]
            for n,pos in enumerate(positions[:4]):
                print("HIT",target,r["id"],r["captured_at"],r["path"],n,
                      raw[max(0,pos-2200):pos+6000].replace("\n"," ")[:8200])
            txt=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
            if txt:
                print("TEXT",target,r["id"],txt[:5000])

# Find recent DOM captures mentioning skill/pet UI and print compact page text.
with server.db_session() as db:
    dom=[dict(r) for r in db.execute("""
      SELECT id,path,page_text,captured_at
      FROM treasure_guide_captures
      WHERE source='dom' AND captured_at>=? AND page_text<>''
      ORDER BY id DESC LIMIT 120
    """,(int(time.time())-6*3600,))]
for r in dom:
    txt=re.sub(r"\s+"," ",str(r.get("page_text") or "")).strip()
    low=txt.lower()
    if any(x in low for x in ["навык","питом","здоров","сражен","монет","провизи","сундук"]):
        print("DOM",r["id"],r["captured_at"],r["path"],txt[:8000])
