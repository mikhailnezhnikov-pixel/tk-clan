from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text(encoding="utf-8")
MARKER="CLAN_SHOP_HISTORY_DEDUPE_V22"

if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)
if "CLAN_SHOP_HISTORY_BUYER_ID_GUARD_V21" not in s:
    raise SystemExit("Clan Shop V21 marker missing")

old='''        event_rows=db.execute("""SELECT week_start,item_type,buyer_player_id AS player_id,
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
'''
new='''        event_rows=db.execute("""WITH dedup AS (
                                      SELECT week_start,item_type,buyer_player_id,buyer_nickname,purchased_at,
                                             MAX(captured_at) AS captured_at
                                      FROM clan_shop_purchase_events
                                      WHERE buyer_player_id<>''
                                      GROUP BY week_start,item_type,buyer_player_id,buyer_nickname,purchased_at
                                  )
                                  SELECT week_start,item_type,buyer_player_id AS player_id,
                                         COUNT(*) AS quantity,MAX(captured_at) AS updated_at
                                  FROM dedup
                                  GROUP BY week_start,item_type,buyer_player_id
                                  ORDER BY week_start DESC,buyer_player_id,item_type""").fetchall()
        unresolved_event_rows=db.execute("""WITH dedup AS (
                                             SELECT week_start,item_type,buyer_nickname,purchased_at,
                                                    MAX(captured_at) AS captured_at
                                             FROM clan_shop_purchase_events
                                             WHERE buyer_player_id='' AND buyer_nickname<>''
                                             GROUP BY week_start,item_type,buyer_nickname,purchased_at
                                         )
                                         SELECT week_start,item_type,buyer_nickname,
                                                COUNT(*) AS quantity,MAX(captured_at) AS updated_at
                                         FROM dedup
                                         GROUP BY week_start,item_type,buyer_nickname
                                         ORDER BY week_start DESC,buyer_nickname,item_type""").fetchall()
'''
if old not in s:
    raise SystemExit("history event query block missing")
s=s.replace(old,new,1)

old2='''        identified=identified_by_week.get(week,{"idol_orbs":0,"splus_businesses":0})
        coverage[week]={
            "shared":shared,
            "identified":identified,
'''
new2='''        identified_raw=identified_by_week.get(week,{"idol_orbs":0,"splus_businesses":0})
        identified={
            "idol_orbs":min(int(identified_raw.get("idol_orbs",0)),int(shared.get("idol_orbs",0))) if int(shared.get("idol_orbs",0))>0 else int(identified_raw.get("idol_orbs",0)),
            "splus_businesses":min(int(identified_raw.get("splus_businesses",0)),int(shared.get("splus_businesses",0))) if int(shared.get("splus_businesses",0))>0 else int(identified_raw.get("splus_businesses",0)),
        }
        coverage[week]={
            "shared":shared,
            "identified":identified,
'''
if old2 not in s:
    raise SystemExit("coverage identified block missing")
s=s.replace(old2,new2,1)

insert_at=s.find("def clan_shop_history_payload()")
if insert_at<0:
    raise SystemExit("history payload missing")
s=s[:insert_at]+"# "+MARKER+"\n"+s[insert_at:]

path.write_text(s,encoding="utf-8")
print("CLAN_SHOP_HISTORY_DEDUPE_V22_PATCH_OK")
