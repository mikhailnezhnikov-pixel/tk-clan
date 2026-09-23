import importlib.util,json
server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec); spec.loader.exec_module(server)
server.ensure_treasure_guide_capture_schema()

with server.db_session() as db:
    rows=[dict(r) for r in db.execute("""SELECT id,player_id,payload_json,captured_at
                                        FROM treasure_guide_captures
                                        WHERE path='/battlepass/claim'
                                          AND payload_json<>''
                                        ORDER BY player_id,id""")]

out=[]
for r in rows:
    try:o=json.loads(r["payload_json"])
    except:continue
    bp=o.get("player_battle_pass") if isinstance(o,dict) else None
    if not isinstance(bp,dict) or bp.get("id")!="bp_event_minigame":continue
    line_counts={}
    for line in bp.get("lines") or []:
        if isinstance(line,dict):
            line_counts[str(line.get("id") or "")]=len(line.get("claimed_levels") or [])
    rew=o.get("reward") if isinstance(o,dict) else None
    if not isinstance(rew,dict):continue
    items=[[x.get("id"),x.get("quantity")] for x in (rew.get("items") or []) if isinstance(x,dict)]
    curs=[[x.get("id"),x.get("quantity")] for x in (rew.get("currencies") or []) if isinstance(x,dict)]
    if not items and not curs:continue
    out.append({
      "id":r["id"],
      "player":str(r["player_id"])[-4:],
      "captured_at":r["captured_at"],
      "counts":line_counts,
      "items":items,
      "currencies":curs
    })
print("CLAIMS",json.dumps(out,ensure_ascii=False))
