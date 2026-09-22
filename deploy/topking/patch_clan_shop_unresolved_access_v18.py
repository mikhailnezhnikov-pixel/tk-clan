from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text(encoding="utf-8")
MARKER="CLAN_SHOP_UNRESOLVED_ACCESS_V18"

if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)
if "CLAN_SHOP_UNRESOLVED_HISTORY_V17" not in s:
    raise SystemExit("Clan Shop V17 marker missing")

old='''            "identity_source":"purchase_history_nickname",
            "cabinet_access":False,
            "cabinet_linked":False,
'''
new='''            "identity_source":"purchase_history_nickname",
            # Nickname-only history is visible but intentionally NOT linked to
            # a cabinet account. Unknown is different from "no cabinet access".
            "cabinet_access":None,
            "cabinet_linked":False,
'''
if old not in s:
    raise SystemExit("unresolved access block missing")
s=s.replace(old,new,1)
s=s.replace("# CLAN_SHOP_UNRESOLVED_HISTORY_V17\n",
            "# CLAN_SHOP_UNRESOLVED_HISTORY_V17\n# "+MARKER+"\n",1)

path.write_text(s,encoding="utf-8")
print("CLAN_SHOP_UNRESOLVED_ACCESS_V18_PATCH_OK")
