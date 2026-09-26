from pathlib import Path
import json,re

p=Path("baseline/topking/HamsterKingMobile.current.user.js")
s=p.read_text(encoding="utf-8")
lines=s.splitlines()

terms=[
  "runFishingAuto","fishingSignature","waitFishingChange","dismissFishingRewards",
  "fairCatalog","costParts","treasureActionButton","treasureModalRoot",
  "fetch(","XMLHttpRequest","409","500","apiRequest","request(","purchase","buy",
  "trader","fair_mini_game_trader","mf_fairlot_minigame_trader"
]

out={"path":str(p),"chars":len(s),"lines":len(lines),"hits":{}}
for term in terms:
    hits=[]
    low=term.lower()
    for i,line in enumerate(lines):
        if low in line.lower():
            a=max(0,i-18); b=min(len(lines),i+50)
            hits.append({
                "line":i+1,
                "context":"\n".join(f"{j+1}: {lines[j]}" for j in range(a,b))
            })
            if len(hits)>=12: break
    out["hits"][term]=hits

Path("audit/userscript-runtime-snippets.json").write_text(
    json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
)
print("USERSCRIPT_RUNTIME_SNIPPETS=PASS")
