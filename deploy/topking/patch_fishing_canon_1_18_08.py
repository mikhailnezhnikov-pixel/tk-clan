# build-trigger: 1.18.08 fishing canon
from pathlib import Path
import sys

target=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=target.read_text(encoding="utf-8")

def need(old,label,count=1):
    actual=s.count(old)
    if actual!=count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")

def rep(old,new,label,count=1):
    global s
    need(old,label,count)
    s=s.replace(old,new,count)

rep(
    "// @version      1.18.07",
    "// @version      1.18.08\n"
    "// @release-note Рыбалка: порядок приведён к подтверждённому канону прохождения. Сначала активируется Проклятая вода, чтобы раскрыть проклятые клетки; затем приоритет Магический питомец → Рыба-фонарь → Существа → Особая вода → обычные воды. Стоимость берётся с карточки/канона, окно награды закрывается перед следующим выбором.",
    "version"
)
rep("const BUILD_VERSION = '1.18.07';","const BUILD_VERSION = '1.18.08';","build")

rep(
    "  const HK_MINIGAME_FLOW_FIXES_REV = 'minigame-flow-fixes-20260926-r1';",
    "  const HK_MINIGAME_FLOW_FIXES_REV = 'minigame-flow-fixes-20260926-r1';\n"
    "  const HK_FISHING_CANON_REV = 'fishing-canon-priority-20260926-r2';",
    "fishing canon marker"
)

old_cost="""    function fishingTileCost(row) {
      const catalogRow=fairCatalog.find(item=>String(item?.lotId||'')===row.lotId);
      const parts=costParts(catalogRow?.cost).filter(part=>part.quantity>0);
      if (parts.length===1) return {id:parts[0].id,quantity:parts[0].quantity};

      const text=clean(row.element?.innerText||row.element?.textContent||'');
      const nums=[...text.matchAll(/(?:^|\s)(\d{1,2})(?=\s|$)/g)]
        .map(match=>Number(match[1]))
        .filter(value=>value>=1 && value<=9);
      const quantity=nums.length ? nums[nums.length-1] : (/calm_water/.test(row.lotId)?1:2);
      return {id:'',quantity};
    }

    function fishingValueTier(lotId) {
      const id=String(lotId||'');
      if (/lamp_fish_water/.test(id)) return 600;
      if (/fishing_water/.test(id)) return 500;
      if (/creatures_water/.test(id)) return 440;
      if (/tornado_water/.test(id)) return 260;
      if (/calm_water/.test(id)) return 120;
      return 0;
    }

    function fishingTarget() {
      const rows=fishingElements().map(row=>{
        const cost=fishingTileCost(row);
        const tier=fishingValueTier(row.lotId);
        const roi=tier/Math.max(1,cost.quantity||1);
        return {...row,cost,tier,roi};
      }).filter(row=>row.tier>0);

      rows.sort((a,b)=>
        b.tier-a.tier ||
        b.roi-a.roi ||
        (a.cost.quantity||99)-(b.cost.quantity||99) ||
        a.index-b.index
      );
      return rows[0] || null;
    }
"""
new_cost="""    function fishingCanonicalCost(lotId) {
      const id=String(lotId||'');
      if (/magic_pet_water_uncursed/.test(id)) return 3;
      if (/^.*is_fishing_cursed_water$/.test(id)) return 3;
      if (/lamp_fish_water_uncursed/.test(id)) return 2;
      if (/creatures_water_uncursed/.test(id)) return 2;
      if (/tornado_cursed_water/.test(id)) return 2;
      if (/tornado_water/.test(id)) return 2;
      if (/fishing_water/.test(id)) return 2;
      if (/calm_water/.test(id)) return 1;
      return 1;
    }

    function fishingTileCost(row) {
      const catalogRow=fairCatalog.find(item=>String(item?.lotId||'')===row.lotId);
      const parts=costParts(catalogRow?.cost).filter(part=>part.quantity>0);
      if (parts.length===1) return {id:parts[0].id,quantity:parts[0].quantity};

      const text=clean(row.element?.innerText||row.element?.textContent||'');
      const nums=[...text.matchAll(/(?:^|\s)(\d{1,2})(?=\s|$)/g)]
        .map(match=>Number(match[1]))
        .filter(value=>value>=1 && value<=9);
      const quantity=nums.length ? nums[nums.length-1] : fishingCanonicalCost(row.lotId);
      return {id:'',quantity};
    }

    function fishingValueTier(lotId,hasCurseTrigger=false) {
      const id=String(lotId||'');

      // Confirmed 24.09 mechanic: the single cursed-water trigger must go first.
      // It converts tornado_cursed cells into valuable uncursed/special cells.
      if (/is_fishing_cursed_water$/.test(id)) return 1200;

      // Do NOT waste casts on pink tornado-cursed cells while the trigger exists.
      if (/tornado_cursed_water/.test(id)) return hasCurseTrigger ? -1000 : 80;

      // Confirmed all-pink run priority consumed the remaining 9 casts exactly:
      // magic pet (3) -> lamp fish (2+2) -> creatures (2).
      if (/magic_pet_water_uncursed/.test(id)) return 1000;
      if (/lamp_fish_water_uncursed/.test(id) || /lamp_fish_water/.test(id)) return 920;
      if (/creatures_water_uncursed/.test(id) || /creatures_water/.test(id)) return 860;

      // Other special water remains above ordinary water.
      if (/fishing_water/.test(id)) return 720;

      // Hurricane water can benefit from the Fishing Map finder skill.
      if (/tornado_water/.test(id)) return 300;

      // Calm cells are the cheapest fallback.
      if (/calm_water_uncursed/.test(id)) return 230;
      if (/calm_water/.test(id)) return 200;
      return 0;
    }

    function fishingTarget() {
      const source=fishingElements();
      const hasCurseTrigger=source.some(row=>/is_fishing_cursed_water$/.test(row.lotId));
      const rows=source.map(row=>{
        const cost=fishingTileCost(row);
        const tier=fishingValueTier(row.lotId,hasCurseTrigger);
        const roi=tier/Math.max(1,cost.quantity||1);
        return {...row,cost,tier,roi};
      }).filter(row=>row.tier>0);

      rows.sort((a,b)=>
        b.tier-a.tier ||
        b.roi-a.roi ||
        (a.cost.quantity||99)-(b.cost.quantity||99) ||
        a.index-b.index
      );
      return rows[0] || null;
    }
"""
rep(old_cost,new_cost,"fishing canon priority")

anchor="""    function failFishingAuto(reason,data={}) {
      try { localStorage.setItem(FISHING_AUTO_STORAGE_KEY,'0'); } catch (_) {}
      fishingAutoRunId+=1;
      fishingAutoRunning=false;
      updateFishingAutoToggle();
      recordDiagnostic('fishing-auto-stop',{revision:HK_FISHING_AUTO_REV,reason,...data});
      return false;
    }

"""
insert="""    async function dismissFishingRewards(runId) {
      let clicked=0;
      for (let i=0;i<6;i++) {
        if (runId!==fishingAutoRunId || !fishingAutoEnabled()) break;
        let button=treasureRewardButton();
        if (!button) {
          await new Promise(resolve=>setTimeout(resolve,180));
          button=treasureRewardButton();
          if (!button) break;
        }
        if (!dispatchBattleTap(button,'fishing-reward-'+(i+1))) break;
        clicked+=1;
        await new Promise(resolve=>setTimeout(resolve,280));
      }
      return clicked;
    }

"""
need(anchor,"fishing reward anchor")
s=s.replace(anchor,anchor+insert,1)

rep(
    """          if (fishingSignature()!==before) {
            recordDiagnostic('fishing-auto-complete',{revision:HK_FISHING_AUTO_REV,lotId:target.lotId,mode:'direct'});
            return true;
          }
""",
    """          if (fishingSignature()!==before) {
            await new Promise(resolve=>setTimeout(resolve,180));
            const rewards=await dismissFishingRewards(runId);
            recordDiagnostic('fishing-auto-complete',{
              revision:HK_FISHING_CANON_REV,
              lotId:target.lotId,
              mode:'direct',
              rewardsDismissed:rewards
            });
            return true;
          }
""",
    "fishing direct reward dismiss"
)

rep(
    """        const changed=await waitFishingChange(before,runId);
        await new Promise(resolve=>setTimeout(resolve,220));
        const rewards=await dismissTreasureRewards(runId);
        if (!changed && rewards===0) {
""",
    """        const changed=await waitFishingChange(before,runId);
        await new Promise(resolve=>setTimeout(resolve,220));
        const rewards=await dismissFishingRewards(runId);
        if (!changed && rewards===0) {
""",
    "fishing modal reward dismiss"
)

rep(
    """          revision:HK_FISHING_AUTO_REV,
          lotId:target.lotId,
          tier:target.tier,
""",
    """          revision:HK_FISHING_CANON_REV,
          lotId:target.lotId,
          tier:target.tier,
""",
    "fishing complete revision"
)

for marker in [
    "// @version      1.18.08",
    "const BUILD_VERSION = '1.18.08';",
    "fishing-canon-priority-20260926-r2",
    "is_fishing_cursed_water$",
    "tornado_cursed_water",
    "magic_pet_water_uncursed",
    "lamp_fish_water_uncursed",
    "creatures_water_uncursed",
    "fishingCanonicalCost",
    "dismissFishingRewards",
    "fishing-reward-",
    "minigame-flow-fixes-20260926-r1",
    "lights-final-reward-20260926-r1",
    "chest-full-dig-first-20260926-r1",
    "battle-entry-before-auto-20260926-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("FISHING_CANON_1_18_08=PASS")
