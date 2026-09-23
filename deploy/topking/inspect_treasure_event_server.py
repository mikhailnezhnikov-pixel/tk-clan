from pathlib import Path
p=Path("/opt/hamsterking-license/server.py")
s=p.read_text(encoding="utf-8")
for marker in [
    "def do_POST",
    'elif path == "/api/v1/clan-shop-events/submit"',
    'elif path == "/api/v1/recipes',
    'elif path == "/api/v1/public/maps"'
]:
    i=s.find(marker)
    print("\n###",marker,"@",i)
    if i>=0:
        print(s[max(0,i-1500):i+12000])
