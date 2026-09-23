from pathlib import Path

s=Path("/opt/hamsterking-license/server.py").read_text(encoding="utf-8")
for marker in ["download_url","latest_version","update_required","HK_MIN_SCRIPT_VERSION"]:
    i=s.find(marker)
    print("\nSERVER_MARKER",marker,i)
    if i>=0:
        print(s[max(0,i-2200):i+5200])
