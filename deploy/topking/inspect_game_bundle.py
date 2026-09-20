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


print("=== MAP ROUTES ===")
routes=sorted(set(re.findall(r'["\x27](/[^"\x27]{1,120})["\x27]',text)))
for route in routes:
    if re.search(r'(map|area|building|district|room|explor|invest|event)',route,re.I):
        print(route)

for term in (
    "gamearea","game_area","building_id","buildingId","room_count","roomCount",
    "crystals","crystal","building_generator","is_investment","investment",
    "event_building","has_events","district","explore","building_rooms",
    "opened","buildings"
):
    print("=== MAP TERM "+term+" ===")
    pos=0
    for _ in range(10):
        pos=text.find(term,pos)
        if pos<0: break
        print(re.sub(r"\s+"," ",text[max(0,pos-650):pos+1650])[:2300])
        pos+=len(term)
