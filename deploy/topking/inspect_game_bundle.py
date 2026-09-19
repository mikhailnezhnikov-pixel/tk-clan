from pathlib import Path
import re, sys

path=Path(sys.argv[1])
text=path.read_text("utf-8","replace")
terms=[
    "Ri.alliance","Ri.members","Ri.list","function Yc","Yc=",
    "alliance_id","allianceId",
    "defense_points","defence_points","defensePoints","defencePoints",
    "hamsters_power","hamstersPower",
    "player_level","playerLevel","leaderboard_type","clan_player_level_lb","hamsters_power_lb","_lb",
    "active_battles","active_defense_wars",
    "warHealth","health"
]
for term in terms:
    print(f"=== TERM {term} ===")
    start=0
    count=0
    while count<8:
        i=text.find(term,start)
        if i<0:
            break
        snippet=text[max(0,i-650):min(len(text),i+1450)]
        snippet=re.sub(r"\s+"," ",snippet)
        print(snippet[:2100])
        start=i+len(term)
        count+=1
