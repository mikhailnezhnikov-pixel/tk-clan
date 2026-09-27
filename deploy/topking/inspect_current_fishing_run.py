from pathlib import Path
p=Path("baseline/topking/HamsterKingMobile.current.user.js")
s=p.read_text(encoding="utf-8")
i=s.find("async function runFishingAuto()")
print("CURRENT_FISHING_RUN")
print(s[i:i+18000] if i>=0 else "NOT_FOUND")
