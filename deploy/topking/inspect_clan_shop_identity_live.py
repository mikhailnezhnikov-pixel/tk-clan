import importlib.util, json, sqlite3, os

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server", server_path)
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

print("SERVER_MARKER", "CLAN_SHOP_IDENTITY_RESOLUTION_V6" in open(server_path, encoding="utf-8").read())
payload=server.clan_shop_history_payload()
print("HISTORY", json.dumps(payload, ensure_ascii=False))

db=sqlite3.connect(server.DB_PATH)
db.row_factory=sqlite3.Row
rows=db.execute("""SELECT clan_key,week_key,snapshot_json,captured_at
                   FROM clan_skill_full_snapshots
                   ORDER BY captured_at DESC LIMIT 5""").fetchall()
wanted={"5112494832","275051195","5262908393","1083594259","1656402180","552583086"}
found={}
for row in rows:
    try:
        doc=json.loads(row["snapshot_json"])
    except Exception:
        continue
    stack=[doc]
    while stack:
        v=stack.pop()
        if isinstance(v,dict):
            pid=str(v.get("player_id") or v.get("playerId") or "").strip()
            nick=str(v.get("nickname") or v.get("name") or "").strip()
            if pid in wanted and nick:
                found.setdefault(pid,nick)
            stack.extend(v.values())
        elif isinstance(v,list):
            stack.extend(v)
print("FULL_SNAPSHOT_NAMES", json.dumps(found, ensure_ascii=False))

skills={}
for row in db.execute("""SELECT player_id,nickname,scanned_at
                         FROM clan_skill_snapshots
                         WHERE player_id IN ('5112494832','275051195','5262908393','1083594259','1656402180','552583086')
                         ORDER BY scanned_at DESC"""):
    pid=str(row["player_id"])
    if pid not in skills and row["nickname"]:
        skills[pid]=row["nickname"]
print("SKILL_NAMES", json.dumps(skills, ensure_ascii=False))


purchase_ids={str(r.get("player_id") or "") for r in payload.get("items",[]) if r.get("player_id")}
linked={}
if purchase_ids:
    placeholders=",".join("?" for _ in purchase_ids)
    q=f"""SELECT linked_player_id,note,first_name,username,active
          FROM clan_members
          WHERE linked_player_id IN ({placeholders})"""
    for row in db.execute(q,tuple(sorted(purchase_ids))):
        linked[str(row["linked_player_id"] or "")]={
            "note":str(row["note"] or ""),
            "first_name":str(row["first_name"] or ""),
            "username":str(row["username"] or ""),
            "active":int(row["active"] or 0),
        }
print("LINKED_MEMBERS",json.dumps(linked,ensure_ascii=False))


try:
    current_week=max((str(r.get("week_start") or "") for r in payload.get("items",[]) if r.get("week_start")),default="")
    print("CURRENT_WEEK",current_week)
    if current_week:
        lots=[dict(r) for r in db.execute("""SELECT week_start,lot_id,item_type,lot_name,reward_id,shared_purchased,shared_maximum,updated_at
                                            FROM clan_shop_actual_lots
                                            WHERE week_start=?
                                            ORDER BY item_type,lot_id""",(current_week,))]
        players=[dict(r) for r in db.execute("""SELECT week_start,lot_id,item_type,player_id,quantity,updated_at
                                               FROM clan_shop_actual_players
                                               WHERE week_start=?
                                               ORDER BY item_type,lot_id,player_id""",(current_week,))]
        print("CURRENT_WEEK_LOTS",json.dumps(lots,ensure_ascii=False))
        print("CURRENT_WEEK_PLAYERS",json.dumps(players,ensure_ascii=False))
except Exception as e:
    print("CURRENT_WEEK_DETAIL_ERROR",repr(e))
