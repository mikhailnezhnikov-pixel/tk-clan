from pathlib import Path
import json

p=Path("baseline/topking/HamsterKingMobile.current.user.js")
s=p.read_text(encoding="utf-8")
lines=s.splitlines()

terms=[
    "const HK_TREASURE_GUIDE_CAPTURE_REV",
    "function treasureGuideSubmit",
    "function acceptTreasureGuideApi",
    "function scanTreasureGuideDom",
    "function scheduleTreasureGuideDomScan",
    "function installTreasureGuideCapture",
    "function installNetworkCapture",
    "acceptTreasureGuideApi(url,body)",
    "acceptTreasureGuideApi(this.__hkUrl,body)",
    "recordDiagnostic(",
    "function licensedServerJson",
    "function treasureGuideScreenVisible",
    "function treasureGuideHash",
    "function treasureRunRecorderTargetInfo",
    "function treasureRunRecorderUpdateButton",
    "treasureRunRecorderObserver=new MutationObserver"
]

out={"path":str(p),"chars":len(s),"lines":len(lines),"hits":{}}
for term in terms:
    hits=[]
    low=term.lower()
    for i,line in enumerate(lines):
        if low in line.lower():
            a=max(0,i-30)
            b=min(len(lines),i+120)
            hits.append({
                "line":i+1,
                "context":"\n".join(f"{j+1}: {lines[j]}" for j in range(a,b))
            })
            if len(hits)>=12:
                break
    out["hits"][term]=hits

Path("audit/treasure-recorder-anchors.json").write_text(
    json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
)
print("TREASURE_RECORDER_ANCHORS=PASS")
