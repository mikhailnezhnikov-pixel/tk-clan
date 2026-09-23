from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text(encoding="utf-8")
MARKER="CLAN_SHOP_HISTORY_BUYER_ID_GUARD_V21"

if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)
if "CLAN_SHOP_DOM_PLAYER_ID_GUARD_V20" not in s:
    raise SystemExit("Clan Shop V20 marker missing")

old='''        db.execute("""UPDATE clan_shop_purchase_events
                      SET buyer_player_id=''
                      WHERE source_path LIKE 'dom:%' AND buyer_player_id<>''""")
'''
new='''        db.execute("""UPDATE clan_shop_purchase_events
                      SET buyer_player_id=''
                      WHERE (source_path LIKE 'dom:%' OR source_path='/clan/shop_history')
                        AND buyer_player_id<>''""")
'''
if old not in s:
    raise SystemExit("V20 cleanup block missing")
s=s.replace(old,new,1)

old2='''            if source_path.startswith("dom:"):
                buyer_player_id=""
'''
new2='''            if source_path.startswith("dom:") or source_path=="/clan/shop_history":
                buyer_player_id=""
'''
if old2 not in s:
    raise SystemExit("V20 submit guard missing")
s=s.replace(old2,new2,1)

insert_at=s.find("def ensure_clan_shop_purchase_event_schema()")
if insert_at<0:
    raise SystemExit("purchase event schema function missing")
s=s[:insert_at]+"# "+MARKER+"\n"+s[insert_at:]

path.write_text(s,encoding="utf-8")
print("CLAN_SHOP_HISTORY_BUYER_ID_GUARD_V21_PATCH_OK")
