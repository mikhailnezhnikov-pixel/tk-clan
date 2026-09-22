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


try:
    rows=[dict(r) for r in db.execute("""SELECT week_start,lot_id,item_type,player_id,quantity,updated_at
                                        FROM clan_shop_actual_players
                                        WHERE week_start IN ('2026-09-14','2026-09-21')
                                        ORDER BY player_id,item_type,week_start""")]
    print("TWO_WEEK_PLAYER_ROWS",json.dumps(rows,ensure_ascii=False))
except Exception as e:
    print("TWO_WEEK_PLAYER_ROWS_ERROR",repr(e))


try:
    current_ids=[str(r["player_id"]) for r in db.execute("""SELECT DISTINCT player_id FROM clan_shop_actual_players
                                                            WHERE week_start='2026-09-21'""")]
    links={}
    if current_ids:
        placeholders=",".join("?" for _ in current_ids)
        q=f"""SELECT linked_player_id,note,first_name,username,active
              FROM clan_members WHERE linked_player_id IN ({placeholders})"""
        for row in db.execute(q,tuple(current_ids)):
            links[str(row["linked_player_id"] or "")]={
                "note":str(row["note"] or ""),
                "first_name":str(row["first_name"] or ""),
                "username":str(row["username"] or ""),
                "active":int(row["active"] or 0),
            }
    print("CURRENT_PLAYER_LINKS",json.dumps(links,ensure_ascii=False))
except Exception as e:
    print("CURRENT_PLAYER_LINKS_ERROR",repr(e))


try:
    selected_ids={"1083594259","1656402180","5112494832","552583086","5225915725","5262908393","275051195"}
    participants=[
        row for row in server.clan_shop_participants()
        if str(row.get("player_id") or "") in selected_ids
    ]
    print("PARTICIPANTS_SELECTED",json.dumps(participants,ensure_ascii=False))
except Exception as e:
    print("PARTICIPANTS_SELECTED_ERROR",repr(e))


try:
    source=open(server_path,encoding="utf-8").read()
    a=source.index("def clan_shop_history_payload() -> dict:")
    b=source.index("\ndef clan_shop_publication_text",a)
    print("HISTORY_SOURCE_BEGIN")
    print(source[a:b])
    print("HISTORY_SOURCE_END")
except Exception as e:
    print("HISTORY_SOURCE_ERROR",repr(e))


try:
    rows=[dict(r) for r in db.execute("""SELECT week_start,item_type,buyer_player_id,buyer_nickname,
                                               COUNT(*) AS purchases,MAX(purchased_at) AS last_purchase,
                                               MAX(captured_at) AS last_capture
                                        FROM clan_shop_purchase_events
                                        GROUP BY week_start,item_type,buyer_player_id,buyer_nickname
                                        ORDER BY week_start DESC,last_purchase DESC""")]
    print("PURCHASE_EVENTS_SUMMARY",json.dumps(rows,ensure_ascii=False))
    recent=[dict(r) for r in db.execute("""SELECT event_key,purchased_at,week_start,buyer_player_id,buyer_nickname,
                                                  lot_id,item_type,lot_name,source_path,captured_by,captured_at
                                           FROM clan_shop_purchase_events
                                           ORDER BY captured_at DESC,purchased_at DESC
                                           LIMIT 80""")]
    print("PURCHASE_EVENTS_RECENT",json.dumps(recent,ensure_ascii=False))
except Exception as e:
    print("PURCHASE_EVENTS_ERROR",repr(e))


try:
    all_participants=server.clan_shop_participants()
    print("PARTICIPANTS_ALL_SUMMARY",json.dumps({
        "count":len(all_participants),
        "unique_player_ids":len({str(r.get("player_id") or "") for r in all_participants if str(r.get("player_id") or "")}),
        "unique_player_keys":len({str(r.get("player_key") or "") for r in all_participants if str(r.get("player_key") or "")}),
        "unique_nicknames_casefold":len({str(r.get("nickname") or "").strip().casefold() for r in all_participants if str(r.get("nickname") or "").strip()}),
    },ensure_ascii=False))
    print("PARTICIPANTS_ALL",json.dumps(all_participants,ensure_ascii=False))
    source=open(server_path,encoding="utf-8").read()
    a=source.index("def clan_shop_participants() -> list[dict]:")
    b=source.index("\ndef ",a+1)
    print("PARTICIPANTS_SOURCE_BEGIN")
    print(source[a:b])
    print("PARTICIPANTS_SOURCE_END")
except Exception as e:
    print("PARTICIPANTS_ALL_ERROR",repr(e))


try:
    full=server.latest_clan_full_snapshot()
    overall=full.get("overall") if isinstance(full,dict) and isinstance(full.get("overall"),list) else []
    selected=[]
    for row in overall:
        if not isinstance(row,dict):
            continue
        nick=str(row.get("nickname") or "")
        if any(token.casefold() in nick.casefold() for token in ("DarkSide","Nivre","Вредн","Снеж","Ariad","Арианд","Manowar","Rajtoo")):
            selected.append(row)
    print("OVERALL_RAW_SELECTED",json.dumps(selected,ensure_ascii=False))
except Exception as e:
    print("OVERALL_RAW_SELECTED_ERROR",repr(e))
