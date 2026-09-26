from pathlib import Path
import json

p=Path("baseline/topking/HamsterKingMobile.current.user.js")
s=p.read_text(encoding="utf-8")
lines=s.splitlines()

terms=[
  "// @version",
  "const BUILD_VERSION",
  "function visible(",
  "function clean(",
  "function getSignature(",
  "function checkPuzzle(",
  "function treasureGuideScreenVisible(",
  "function treasureGuideHash(",
  "function treasureModalRoot(",
  "function treasureActionButton(",
  "function dismissTreasureRewards(",
  "function dispatchBattleTap(",
  "function battleAutoEnabled(",
  "function setBattleAutoEnabled(",
  "async function runBattle(",
  "async function runBattleVictoryClaim(",
  "function fishingAutoEnabled(",
  "function setFishingAutoEnabled(",
  "async function runFishingAuto(",
  "function traderAutoEnabled(",
  "function setTraderAutoEnabled(",
  "async function runTraderAuto(",
  "function chestAutoEnabled(",
  "function setChestAutoEnabled(",
  "async function runTreasureChestAuto(",
  "function lightsAutoEnabled(",
  "function setLightsAutoEnabled(",
  "async function runLightsAuto(",
  "function treasureChestElements(",
  "function fishingElements(",
  "function traderElements(",
  "const fairCatalog",
  "function costParts(",
  "function walletAmount(",
  "function debitWallet(",
  "mf_treasurelot_active_",
  "fair_treasures",
  "Начать новое путешествие",
  "Покинуть локацию",
  "function recordDiagnostic(",
  "TREASURE_RUN_RECORDER",
  "async function runAutoMapTick",
  "function setAutoMapEnabled",
  "function autoMapJourneyButton",
  "function autoMapMapCards",
  "function dispatchAutoMapTap",
  "function autoMapStartLockAt",
  "function treasureChestTarget(",
  "function treasureChestSignature("
]

out={"path":str(p),"chars":len(s),"lines":len(lines),"hits":{}}
for term in terms:
    hits=[]
    low=term.lower()
    for i,line in enumerate(lines):
        if low in line.lower():
            a=max(0,i-35); b=min(len(lines),i+120)
            hits.append({
              "line":i+1,
              "context":"\n".join(f"{j+1}: {lines[j]}" for j in range(a,b))
            })
            if len(hits)>=10: break
    out["hits"][term]=hits

Path("audit/treasure-auto-anchors.json").write_text(
    json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
)
print("TREASURE_AUTO_ANCHORS=PASS")

print("PRINT_AUTOMAP_CURRENT_CONTEXT")
for key in ["async function runAutoMapTick","function setAutoMapEnabled","function autoMapJourneyButton","function autoMapMapCards","function dispatchAutoMapTap","function autoMapStartLockAt"]:
    print("=== "+key+" ===")
    for hit in out["hits"].get(key,[])[:1]:
        print(hit["context"])

print("PRINT_CHEST_CURRENT_CONTEXT")
for key in ["function treasureChestElements(","function treasureChestTarget(","async function runTreasureChestAuto(","function treasureChestSignature("]:
    print("=== "+key+" ===")
    for hit in out["hits"].get(key,[])[:1]:
        print(hit["context"])
