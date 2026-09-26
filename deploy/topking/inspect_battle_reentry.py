from pathlib import Path
import json

p=Path("baseline/topking/HamsterKingMobile.current.user.js")
s=p.read_text(encoding="utf-8")
lines=s.splitlines()
terms=[
 "runBattle","runBattleEntry","battleNeedsEntry","battleSignature","battleElements",
 "battleAutoRunning","lastSignature","isBattle","battleTarget","battle-auto",
 "mf_treasurelot_sword_","mf_treasurelot_battle","enemy","battleEntry"
]
out={"chars":len(s),"lines":len(lines),"hits":{}}
for term in terms:
    hits=[]
    low=term.lower()
    for i,line in enumerate(lines):
        if low in line.lower():
            a=max(0,i-35); b=min(len(lines),i+80)
            hits.append({"line":i+1,"context":"\n".join(f"{j+1}: {lines[j]}" for j in range(a,b))})
            if len(hits)>=10: break
    out["hits"][term]=hits
Path("audit/battle-reentry-snippets.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("BATTLE_REENTRY_INSPECT=PASS")
