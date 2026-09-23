from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text(encoding="utf-8")
MARKER="CLAN_SHOP_HISTORY_SESSION_DEDUPE_V23"

if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)
if "CLAN_SHOP_HISTORY_DEDUPE_V22" not in s:
    raise SystemExit("Clan Shop V22 marker missing")

old='''        event_rows=db.execute("""WITH dedup AS (
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
new='''        event_rows=db.execute("""WITH session_counts AS (
                                      SELECT week_start,item_type,buyer_player_id,buyer_nickname,purchased_at,
                                             captured_by,captured_at,COUNT(*) AS qty
                                      FROM clan_shop_purchase_events
                                      WHERE buyer_player_id<>''
                                      GROUP BY week_start,item_type,buyer_player_id,buyer_nickname,purchased_at,captured_by,captured_at
                                  ), dedup AS (
                                      SELECT week_start,item_type,buyer_player_id,buyer_nickname,purchased_at,
                                             MAX(qty) AS qty,MAX(captured_at) AS captured_at
                                      FROM session_counts
                                      GROUP BY week_start,item_type,buyer_player_id,buyer_nickname,purchased_at
                                  )
                                  SELECT week_start,item_type,buyer_player_id AS player_id,
                                         SUM(qty) AS quantity,MAX(captured_at) AS updated_at
                                  FROM dedup
                                  GROUP BY week_start,item_type,buyer_player_id
                                  ORDER BY week_start DESC,buyer_player_id,item_type""").fetchall()
        unresolved_event_rows=db.execute("""WITH session_counts AS (
                                             SELECT week_start,item_type,buyer_nickname,purchased_at,
                                                    captured_by,captured_at,COUNT(*) AS qty
                                             FROM clan_shop_purchase_events
                                             WHERE buyer_player_id='' AND buyer_nickname<>''
                                             GROUP BY week_start,item_type,buyer_nickname,purchased_at,captured_by,captured_at
                                         ), dedup AS (
                                             SELECT week_start,item_type,buyer_nickname,purchased_at,
                                                    MAX(qty) AS qty,MAX(captured_at) AS captured_at
                                             FROM session_counts
                                             GROUP BY week_start,item_type,buyer_nickname,purchased_at
                                         )
                                         SELECT week_start,item_type,buyer_nickname,
                                                SUM(qty) AS quantity,MAX(captured_at) AS updated_at
                                         FROM dedup
                                         GROUP BY week_start,item_type,buyer_nickname
                                         ORDER BY week_start DESC,buyer_nickname,item_type""").fetchall()
'''
if old not in s:
    raise SystemExit("V22 event query block missing")
s=s.replace(old,new,1)

insert_at=s.find("def clan_shop_history_payload()")
if insert_at<0:
    raise SystemExit("history payload missing")
s=s[:insert_at]+"# "+MARKER+"\n"+s[insert_at:]

path.write_text(s,encoding="utf-8")
print("CLAN_SHOP_HISTORY_SESSION_DEDUPE_V23_PATCH_OK")
