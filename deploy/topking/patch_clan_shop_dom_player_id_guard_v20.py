from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text(encoding="utf-8")
MARKER="CLAN_SHOP_DOM_PLAYER_ID_GUARD_V20"

if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)

if "CLAN_SHOP_CURRENT_ROSTER_ONLY_V19" not in s and "CLAN_SHOP_UNRESOLVED_ACCESS_V18" not in s:
    raise SystemExit("Clan Shop base marker missing")

old='''        db.execute("""CREATE INDEX IF NOT EXISTS idx_clan_shop_purchase_events_week
                      ON clan_shop_purchase_events(week_start,item_type,buyer_player_id)""")
'''
new='''        db.execute("""CREATE INDEX IF NOT EXISTS idx_clan_shop_purchase_events_week
                      ON clan_shop_purchase_events(week_start,item_type,buyer_player_id)""")
        # DOM-derived history can contain unrelated numeric ids on parent nodes.
        # Keep DOM events nickname-only unless the game API itself provides a
        # trustworthy buyer id through a non-DOM source.
        db.execute("""UPDATE clan_shop_purchase_events
                      SET buyer_player_id=''
                      WHERE source_path LIKE 'dom:%' AND buyer_player_id<>''""")
'''
if old in s:
    s=s.replace(old,new,1)

old2='''            buyer_player_id=str(raw.get("buyer_player_id") or "").strip()[:80]
            if buyer_player_id and not buyer_player_id.isdigit():
                continue
            buyer_nickname=str(raw.get("buyer_nickname") or "").strip()[:160]
            lot_id=str(raw.get("lot_id") or "").strip()[:180]
            lot_name=str(raw.get("lot_name") or "").strip()[:320]
            source_path=str(raw.get("source_path") or "").strip()[:240]
'''
new2='''            source_path=str(raw.get("source_path") or "").strip()[:240]
            buyer_player_id=str(raw.get("buyer_player_id") or "").strip()[:80]
            if source_path.startswith("dom:"):
                buyer_player_id=""
            if buyer_player_id and not buyer_player_id.isdigit():
                continue
            buyer_nickname=str(raw.get("buyer_nickname") or "").strip()[:160]
            lot_id=str(raw.get("lot_id") or "").strip()[:180]
            lot_name=str(raw.get("lot_name") or "").strip()[:320]
'''
if old2 in s:
    s=s.replace(old2,new2,1)
elif "if source_path.startswith("dom:"):" not in s:
    raise SystemExit("submit identity block missing")

insert_at=s.find("def ensure_clan_shop_purchase_event_schema()")
if insert_at<0:
    raise SystemExit("purchase event schema function missing")
s=s[:insert_at]+"# "+MARKER+"\n"+s[insert_at:]

path.write_text(s,encoding="utf-8")
print("CLAN_SHOP_DOM_PLAYER_ID_GUARD_V20_PATCH_OK")
