from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text(encoding="utf-8")
MARKER="CLAN_SHOP_UNRESOLVED_HISTORY_V17"

if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)
if "CLAN_SHOP_PURCHASE_EVENTS_V16" not in s:
    raise SystemExit("Clan Shop V16 marker missing")

start=s.index("def clan_shop_history_payload() -> dict:")
end=s.index("\ndef clan_shop_publication_text",start)
h=s[start:end]

old='''        event_rows=db.execute("""SELECT week_start,item_type,buyer_player_id AS player_id,
                                        COUNT(*) AS quantity,MAX(captured_at) AS updated_at
                                 FROM clan_shop_purchase_events
                                 WHERE buyer_player_id<>''
                                 GROUP BY week_start,item_type,buyer_player_id
                                 ORDER BY week_start DESC,buyer_player_id,item_type""").fetchall()

    merged_player_rows={}
'''
new='''        event_rows=db.execute("""SELECT week_start,item_type,buyer_player_id AS player_id,
                                        COUNT(*) AS quantity,MAX(captured_at) AS updated_at
                                 FROM clan_shop_purchase_events
                                 WHERE buyer_player_id<>''
                                 GROUP BY week_start,item_type,buyer_player_id
                                 ORDER BY week_start DESC,buyer_player_id,item_type""").fetchall()
        unresolved_event_rows=db.execute("""SELECT week_start,item_type,buyer_nickname,
                                                   COUNT(*) AS quantity,MAX(captured_at) AS updated_at
                                            FROM clan_shop_purchase_events
                                            WHERE buyer_player_id='' AND buyer_nickname<>''
                                            GROUP BY week_start,item_type,buyer_nickname
                                            ORDER BY week_start DESC,buyer_nickname,item_type""").fetchall()

    merged_player_rows={}
'''
if old not in h:
    raise SystemExit("event query block missing")
h=h.replace(old,new,1)

needle='''    coverage={}
    all_weeks=set(shared_by_week)|set(identified_by_week)
'''
insert='''    # CLAN_SHOP_UNRESOLVED_HISTORY_V17
    # Rows from the authoritative in-game purchase history may expose a game
    # nickname before they expose an exact player_id. Show those rows as
    # unlinked history identities, but NEVER bind them to cabinet users by
    # nickname. If the same event is later captured with player_id, the event
    # upsert resolves it and this temporary row disappears automatically.
    for row in unresolved_event_rows:
        quantity=max(0,int(row["quantity"] or 0))
        if quantity<=0:
            continue
        week=str(row["week_start"] or "")
        item_type=str(row["item_type"] or "")
        nickname=str(row["buyer_nickname"] or "").strip()
        if not week or item_type not in ("idol_orbs","splus_businesses") or not nickname:
            continue
        key=(week,"history-nick:"+nickname.casefold())
        item=aggregated.setdefault(key,{
            "week_start":week,
            "player_key":"history-nick:"+nickname,
            "player_id":"",
            "nickname":nickname,
            "identity_source":"purchase_history_nickname",
            "cabinet_access":False,
            "cabinet_linked":False,
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
'''
if needle not in h:
    raise SystemExit("coverage anchor missing")
h=h.replace(needle,insert,1)

s=s[:start]+h+s[end:]
# visible marker
s=s.replace("# CLAN_SHOP_PURCHASE_EVENTS_V16\n", "# CLAN_SHOP_PURCHASE_EVENTS_V16\n# "+MARKER+"\n",1)
path.write_text(s,encoding="utf-8")
print("CLAN_SHOP_UNRESOLVED_HISTORY_V17_PATCH_OK")
