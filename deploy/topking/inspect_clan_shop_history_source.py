from pathlib import Path
s=Path("/opt/hamsterking-license/server.py").read_text(encoding="utf-8")
a=s.index("def clan_shop_history_payload() -> dict:")
b=s.index("\ndef clan_shop_publication_text",a)
print(s[a:b])
