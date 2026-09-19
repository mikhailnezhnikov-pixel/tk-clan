from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="CLAN_WAR_HP_SERVER_V1"
if MARKER in s:
    print("CLAN_WAR_HP_SERVER_V1_ALREADY_PRESENT")
    raise SystemExit(0)

old='''    for key in ("our_score", "opponent_score", "started_at", "ends_at"):
        try:
            number = int(value.get(key) or 0)
        except (TypeError, ValueError):
            number = 0
        result[key] = max(0, min(number, 10**18))
    if not result["our_clan"] or not result["opponent"]:
'''
new='''    # CLAN_WAR_HP_SERVER_V1
    for key in ("our_score", "opponent_score", "started_at", "ends_at"):
        try:
            number = int(value.get(key) or 0)
        except (TypeError, ValueError):
            number = 0
        result[key] = max(0, min(number, 10**18))
    for key in ("our_hp", "our_hp_max", "opponent_hp", "opponent_hp_max"):
        if key not in value:
            continue
        try:
            number = int(value.get(key))
        except (TypeError, ValueError):
            continue
        result[key] = max(0, min(number, 10**18))
    if not result["our_clan"] or not result["opponent"]:
'''
if old not in s:
    raise SystemExit("normalize_clan_war anchor missing")
s=s.replace(old,new,1)
path.write_text(s)
print("CLAN_WAR_HP_SERVER_V1_PATCH_OK")
