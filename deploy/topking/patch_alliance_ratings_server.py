from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="ALLIANCE_RATINGS_SERVER_V1"
if MARKER in s:
    print("ALLIANCE_RATINGS_SERVER_V1_ALREADY_PRESENT")
    raise SystemExit(0)

old='RATING_KINDS = frozenset({"influence", "power", "clans", "alliances"})'
new='''# ALLIANCE_RATINGS_SERVER_V1
RATING_KINDS = frozenset({
    "influence", "power", "clans", "alliances",
    "alliance_power", "alliance_influence", "alliance_defense",
})'''
if old not in s:
    raise SystemExit("RATING_KINDS anchor missing")
s=s.replace(old,new,1)

path.write_text(s)
print("ALLIANCE_RATINGS_SERVER_V1_PATCH_OK")
