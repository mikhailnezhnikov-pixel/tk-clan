from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text(encoding="utf-8")
MARKER="CLAN_SHOP_PLAYER_ATTRIBUTION_V10"
if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)
if "CLAN_SHOP_LINKED_PLAYER_ID_V8" not in s:
    raise SystemExit("linked_player_id V8 marker missing")

start_marker="def clan_shop_history_payload() -> dict:\n"
end_marker="\ndef clan_shop_publication_text(payload: dict) -> str:\n"
if start_marker not in s or end_marker not in s:
    raise SystemExit("history anchors missing")
start=s.index(start_marker)
end=s.index(end_marker,start)

new_func=r'''def clan_shop_history_payload() -> dict:
    # CLAN_SHOP_PLAYER_ATTRIBUTION_V10
    # Clan Shop PLAYER and CLAN limits are current-cycle counters in the game.
    # History therefore stores and displays the current week's per-player
    # counters directly. The shared CLAN counter is only a reconciliation total;
    # it must never become a fake "unattributed player" row.
    ensure_clan_shop_schema()
    participants=clan_shop_participants()
    by_player_id={
        str(row.get("player_id") or ""): row
        for row in participants if row.get("player_id")
    }
    linked_identities=clan_shop_linked_identities()

    latest_nickname_by_player_id={}
    full_snapshot_nickname_by_player_id={}
    with db_session() as db:
        try:
            for row in db.execute("""
                SELECT s.player_id,s.nickname
                FROM clan_skill_snapshots AS s
                JOIN (
                    SELECT player_id,MAX(scanned_at) AS scanned_at
                    FROM clan_skill_snapshots
                    WHERE nickname<>''
                    GROUP BY player_id
                ) AS latest
                  ON latest.player_id=s.player_id AND latest.scanned_at=s.scanned_at
                WHERE s.nickname<>''
            """).fetchall():
                pid=str(row["player_id"] or "").strip()
                nickname=str(row["nickname"] or "").strip()
                if pid and nickname:
                    latest_nickname_by_player_id[pid]=nickname
        except sqlite3.Error:
            pass

        try:
            snapshot_rows=db.execute("""
                SELECT snapshot_json,captured_at
                FROM clan_skill_full_snapshots
                ORDER BY captured_at DESC
                LIMIT 24
            """).fetchall()
            for snapshot_row in snapshot_rows:
                try:
                    document_value=json.loads(snapshot_row["snapshot_json"] or "{}")
                except (json.JSONDecodeError,TypeError):
                    continue
                stack=[document_value]
                while stack:
                    value=stack.pop()
                    if isinstance(value,dict):
                        pid=str(value.get("player_id") or value.get("playerId") or "").strip()
                        nickname=str(value.get("nickname") or value.get("name") or "").strip()
                        if pid and nickname and pid not in full_snapshot_nickname_by_player_id:
                            full_snapshot_nickname_by_player_id[pid]=nickname
                        stack.extend(value.values())
                    elif isinstance(value,list):
                        stack.extend(value)
        except sqlite3.Error:
            pass

        lots=db.execute("""SELECT week_start,lot_id,item_type,lot_name,reward_id,
                                  shared_purchased,shared_maximum,updated_at
                           FROM clan_shop_actual_lots
                           ORDER BY week_start DESC,lot_id""").fetchall()
        player_rows=db.execute("""SELECT week_start,lot_id,item_type,player_id,quantity,updated_at
                                  FROM clan_shop_actual_players
                                  ORDER BY week_start DESC,lot_id,player_id""").fetchall()

    shared_by_week={}
    for lot in lots:
        week=str(lot["week_start"])
        item_type=str(lot["item_type"])
        shared_by_week.setdefault(week,{"idol_orbs":0,"splus_businesses":0})
        shared_by_week[week][item_type]+=max(0,int(lot["shared_purchased"] or 0))

    aggregated={}
    identified_by_week={}
    for row in player_rows:
        quantity=max(0,int(row["quantity"] or 0))
        if quantity<=0:
            continue
        week=str(row["week_start"])
        item_type=str(row["item_type"])
        pid=str(row["player_id"] or "").strip()
        if not pid:
            continue

        participant=by_player_id.get(pid)
        linked=linked_identities.get(pid)
        nickname=(
            str(linked.get("display_name") or "").strip() if linked else ""
        ) or (
            str(participant.get("nickname") or "").strip() if participant else ""
        ) or full_snapshot_nickname_by_player_id.get(pid,"") \
          or latest_nickname_by_player_id.get(pid,"") \
          or pid

        key=(week,"id:"+pid)
        item=aggregated.setdefault(key,{
            "week_start":week,
            "player_key":"id:"+pid,
            "player_id":pid,
            "nickname":nickname,
            "identity_source":"linked_player_id" if linked else (
                "clan_snapshot" if participant or pid in full_snapshot_nickname_by_player_id
                else ("skill_snapshot" if pid in latest_nickname_by_player_id else "player_id")
            ),
            "idol_orbs":0,
            "splus_businesses":0,
            "recorded_at":0,
            "is_unattributed":False,
        })
        item[item_type]+=quantity
        item["recorded_at"]=max(item["recorded_at"],int(row["updated_at"] or 0))
        identified_by_week.setdefault(week,{"idol_orbs":0,"splus_businesses":0})
        identified_by_week[week][item_type]+=quantity

    coverage={}
    all_weeks=set(shared_by_week)|set(identified_by_week)
    for week in all_weeks:
        shared=shared_by_week.get(week,{"idol_orbs":0,"splus_businesses":0})
        identified=identified_by_week.get(week,{"idol_orbs":0,"splus_businesses":0})
        coverage[week]={
            "shared":shared,
            "identified":identified,
            "pending":{
                "idol_orbs":max(0,int(shared.get("idol_orbs",0))-int(identified.get("idol_orbs",0))),
                "splus_businesses":max(0,int(shared.get("splus_businesses",0))-int(identified.get("splus_businesses",0))),
            },
        }

    items=list(aggregated.values())
    items.sort(key=lambda row:(row["week_start"],row["nickname"].casefold()),reverse=True)
    return {
        "ok":True,
        "source":"game_actual",
        "counter_mode":"current_cycle_player_counters",
        "items":items,
        "coverage":coverage,
    }

'''
s=s[:start]+new_func+s[end:]
path.write_text(s,encoding="utf-8")
print("CLAN_SHOP_PLAYER_ATTRIBUTION_V10_PATCH_OK")
