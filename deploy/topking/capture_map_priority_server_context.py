from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else '/opt/hamsterking-license/server.py')
s=p.read_text(encoding='utf-8')
terms=[
 'def submit_map_area(',
 'def import_hk_map_room_knowledge(',
 'def hk_map_points_with_canonical(',
 'def _full235_import_row_sql(',
 'def merge_canonical_map_areas(',
 'def load_live_game_geometry_hk_map(',
]
out=[]
for term in terms:
    start=0;n=0
    while True:
        i=s.find(term,start)
        if i<0:break
        n+=1
        out.append(f"\n===== {term} #{n} @ {i} =====\n{s[max(0,i-2500):min(len(s),i+22000)]}\n")
        start=i+len(term)
        if n>=3:break
print(''.join(out))
