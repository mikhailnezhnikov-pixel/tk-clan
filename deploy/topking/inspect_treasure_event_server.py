from pathlib import Path
p=Path("/opt/hamsterking-license/server.py")
s=p.read_text(encoding="utf-8")
for marker in ["def do_GET", "def do_POST", "def read_json", "def recipe_player"]:
    i=s.find(marker)
    print("\n###",marker,"@",i)
    if i>=0:
        print(s[max(0,i-1200):i+9000])
