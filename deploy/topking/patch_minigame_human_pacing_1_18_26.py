from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count:
        raise SystemExit(f"{label}: expected {count} got {n}")
    s=s.replace(old,new,count)

rep("// @version      1.18.25",
    "// @version      1.18.26\n// @release-note Темп автоматизации: покупки и мини-игры переведены на последовательный человеческий ритм — пауза на пересканирование поля, отдельная пауза перед открытием лота, чтением окна и подтверждением, затем ожидание ответа/изменения поля перед следующим действием. 409/429/5xx получили увеличенный cooldown без мгновенных повторов.",
    "version")
rep("const BUILD_VERSION = '1.18.25';",
    "const BUILD_VERSION = '1.18.26';",
    "build")
rep("  const HK_FISHING_BUDGET_REV='fishing-live-budget-20260927-r1';",
    "  const HK_FISHING_BUDGET_REV='fishing-live-budget-20260927-r1';\n  const HK_MINIGAME_HUMAN_PACING_REV='minigame-human-pacing-20260927-r1';",
    "revision")

rep("    const BATTLE_AUTO_SETTLE_MS = 260;",
    "    const BATTLE_AUTO_SETTLE_MS = 1200;",
    "battle settle")
rep("    const LIGHTS_AUTO_SETTLE_MS = 240;",
    "    const LIGHTS_AUTO_SETTLE_MS = 1600;",
    "lights settle")
rep("    const FISHING_MIN_NEXT_ACTION_GAP_MS = 1800;",
    "    const FISHING_MIN_NEXT_ACTION_GAP_MS = 2800;",
    "fishing gap")
rep("    const TRADER_MIN_NEXT_ACTION_GAP_MS = 1800;",
    "    const TRADER_MIN_NEXT_ACTION_GAP_MS = 2800;",
    "trader gap")
rep("    const AUTO_MAP_ACTION_GAP_MS=1450;",
    "    const AUTO_MAP_ACTION_GAP_MS=2400;",
    "auto map gap")

anchor="""    function minigameRecentHttpError(since=0,windowMs=8000) {
"""
if s.count(anchor)!=1:
    raise SystemExit("minigame error anchor missing")
helper="""    function minigameRandomMs(minMs,maxMs) {
      const min=Math.max(0,Math.round(Number(minMs)||0));
      const max=Math.max(min,Math.round(Number(maxMs)||min));
      return min+Math.floor(Math.random()*(max-min+1));
    }

    async function minigameHumanPause(stage='scan',data={}) {
      const ranges={
        scan:[850,1450],
        aim:[550,950],
        confirm:[950,1650],
        settle:[1500,2400],
        reward:[650,1050],
        map:[700,1250]
      };
      const range=ranges[stage] || ranges.scan;
      const waitMs=minigameRandomMs(range[0],range[1]);
      recordDiagnostic('minigame-human-pause',{
        revision:HK_MINIGAME_HUMAN_PACING_REV,
        stage,
        waitMs,
        ...data
      });
      await new Promise(resolve=>setTimeout(resolve,waitMs));
      return waitMs;
    }

"""
s=s.replace(anchor,helper+anchor,1)

old_backoff="""    function minigameBackoffMs(error,streak=0) {
      const status=Number(error?.status||0);
      if (status>=500) return Math.min(10000,5000+Math.max(0,streak)*1200);
      if (status===409) return Math.min(7000,2800+Math.max(0,streak)*800);
      return Math.min(8000,1800+Math.max(0,streak)*900);
    }
"""
new_backoff="""    function minigameBackoffMs(error,streak=0) {
      const status=Number(error?.status||0);
      const n=Math.max(0,Number(streak)||0);
      if (status===429) return Math.min(30000,minigameRandomMs(14000,19000)+n*1800);
      if (status>=500) return Math.min(22000,minigameRandomMs(8000,12000)+n*1400);
      if (status===409) return Math.min(16000,minigameRandomMs(5000,8000)+n*1100);
      return Math.min(14000,minigameRandomMs(3500,5500)+n*900);
    }
"""
rep(old_backoff,new_backoff,"backoff")

# Fishing: re-evaluate the target after a natural scan pause, then wait before opening/confirming.
rep("""      const target=fishingTarget();
      if (!target) {
""",
"""      let target=fishingTarget();
      if (!target) {
""",
"fishing target let")
rep("""      await waitMutationGap(fishingLastMutationAt,FISHING_MIN_NEXT_ACTION_GAP_MS);
      if (!fishingAutoEnabled()) return false;
      if (!fishingAffordable(target.cost)) {
""",
"""      await waitMutationGap(fishingLastMutationAt,FISHING_MIN_NEXT_ACTION_GAP_MS);
      if (!fishingAutoEnabled()) return false;
      await minigameHumanPause('scan',{module:'fishing'});
      if (!fishingAutoEnabled()) return false;
      target=fishingTarget();
      if (!target) return false;
      if (!fishingAffordable(target.cost)) {
""",
"fishing rescan")
rep("""      try {
        if (!dispatchAutoMapTap(target.element,'fishing-open-'+target.lotId)) {
""",
"""      try {
        await minigameHumanPause('aim',{module:'fishing',lotId:target.lotId});
        if (runId!==fishingAutoRunId || !fishingAutoEnabled()) return false;
        if (!fishingAffordable(target.cost)) return false;
        if (!dispatchAutoMapTap(target.element,'fishing-open-'+target.lotId)) {
""",
"fishing aim")
rep("""        if (!fishingAffordable(target.cost)) {
          const close=[...modal.querySelectorAll('button,[role="button"],a,div,span')]
""",
"""        await minigameHumanPause('confirm',{module:'fishing',lotId:target.lotId});
        if (runId!==fishingAutoRunId || !fishingAutoEnabled()) return false;

        if (!fishingAffordable(target.cost)) {
          const close=[...modal.querySelectorAll('button,[role="button"],a,div,span')]
""",
"fishing confirm pause")
rep("""        fishingFailureStreak=0;
        fishingRetryNotBefore=0;
        await waitMutationGap(fishingLastMutationAt,FISHING_MIN_NEXT_ACTION_GAP_MS);
        recordDiagnostic('fishing-auto-complete',{
""",
"""        fishingFailureStreak=0;
        fishingRetryNotBefore=0;
        await minigameHumanPause('settle',{module:'fishing',lotId:target.lotId});
        await waitMutationGap(fishingLastMutationAt,FISHING_MIN_NEXT_ACTION_GAP_MS);
        recordDiagnostic('fishing-auto-complete',{
""",
"fishing settle")

# Rewards: do not acknowledge multiple windows in a few hundred ms.
rep("""        if (!dispatchAutoMapTap(button,'fishing-reward-'+(i+1))) break;
        clicked+=1;
        await new Promise(resolve=>setTimeout(resolve,280));
""",
"""        await minigameHumanPause('reward',{module:'fishing',index:i+1});
        if (!dispatchAutoMapTap(button,'fishing-reward-'+(i+1))) break;
        clicked+=1;
        await minigameHumanPause('settle',{module:'fishing-reward',index:i+1});
""",
"fishing reward pacing")

# Trader: natural scan -> reselect -> aim -> modal reading -> confirm -> settle.
rep("""      const target=traderTarget();
      if (!target) {
""",
"""      let target=traderTarget();
      if (!target) {
""",
"trader target let")
rep("""      await waitMutationGap(traderLastMutationAt,TRADER_MIN_NEXT_ACTION_GAP_MS);
      if (!traderAutoEnabled()) return false;

      traderAutoRunning=true;
""",
"""      await waitMutationGap(traderLastMutationAt,TRADER_MIN_NEXT_ACTION_GAP_MS);
      if (!traderAutoEnabled()) return false;
      await minigameHumanPause('scan',{module:'trader'});
      if (!traderAutoEnabled()) return false;
      target=traderTarget();
      if (!target) return false;

      traderAutoRunning=true;
""",
"trader rescan")
rep("""      try {
        if (!dispatchAutoMapTap(target.element,'trader-open-'+target.lotId)) {
""",
"""      try {
        await minigameHumanPause('aim',{module:'trader',lotId:target.lotId});
        if (runId!==traderAutoRunId || !traderAutoEnabled()) return false;
        if (!dispatchAutoMapTap(target.element,'trader-open-'+target.lotId)) {
""",
"trader aim")
rep("""        if (!action || !dispatchAutoMapTap(action,'trader-confirm-'+target.lotId)) {
""",
"""        await minigameHumanPause('confirm',{module:'trader',lotId:target.lotId});
        if (runId!==traderAutoRunId || !traderAutoEnabled()) return false;

        if (!action || !dispatchAutoMapTap(action,'trader-confirm-'+target.lotId)) {
""",
"trader confirm")
rep("""        traderSessionPurchases+=1;
        traderFailureStreak=0;
        traderRetryNotBefore=0;
        if (target.cost.raw) debitWallet(target.cost.raw,1);
        await waitMutationGap(traderLastMutationAt,TRADER_MIN_NEXT_ACTION_GAP_MS);
""",
"""        traderSessionPurchases+=1;
        traderFailureStreak=0;
        traderRetryNotBefore=0;
        if (target.cost.raw) debitWallet(target.cost.raw,1);
        await minigameHumanPause('settle',{module:'trader',lotId:target.lotId});
        await waitMutationGap(traderLastMutationAt,TRADER_MIN_NEXT_ACTION_GAP_MS);
""",
"trader settle")

# Chest runner: scan/reselect, aim, confirm, reward, settle.
rep("""    async function runTreasureChestAuto() {
      if (!chestAutoEnabled() || chestAutoRunning || battleAutoRunning) return false;
      const target=treasureChestTarget();
      if (!target) return false;

      chestAutoRunning=true;
""",
"""    async function runTreasureChestAuto() {
      if (!chestAutoEnabled() || chestAutoRunning || battleAutoRunning) return false;
      let target=treasureChestTarget();
      if (!target) return false;
      await minigameHumanPause('scan',{module:'chests'});
      if (!chestAutoEnabled()) return false;
      target=treasureChestTarget();
      if (!target) return false;

      chestAutoRunning=true;
""",
"chest scan")
rep("""      try {
        if (runId!==chestAutoRunId || !chestAutoEnabled()) return false;
        dispatchAutoMapTap(target.element,target.digging?'chest-dig-spot':'chest-open-card');

        const modal=await waitTreasureModal(target.cost,runId);
""",
"""      try {
        if (runId!==chestAutoRunId || !chestAutoEnabled()) return false;
        await minigameHumanPause('aim',{module:'chests',lotId:target.lotId});
        if (runId!==chestAutoRunId || !chestAutoEnabled()) return false;
        dispatchAutoMapTap(target.element,target.digging?'chest-dig-spot':'chest-open-card');

        const modal=await waitTreasureModal(target.cost,runId);
""",
"chest aim")
rep("""        let action=await waitTreasureActionButton(modal,target.cost,runId);
        let tapped=false;
        if (action) tapped=dispatchAutoMapTap(action,target.digging?'chest-dig-confirm':'chest-open-confirm');
""",
"""        let action=await waitTreasureActionButton(modal,target.cost,runId);
        await minigameHumanPause('confirm',{module:'chests',lotId:target.lotId});
        if (runId!==chestAutoRunId || !chestAutoEnabled()) return false;
        let tapped=false;
        if (action) tapped=dispatchAutoMapTap(action,target.digging?'chest-dig-confirm':'chest-open-confirm');
""",
"chest confirm")
rep("""        await new Promise(resolve=>setTimeout(resolve,220));
        const rewards=await dismissTreasureRewards(runId);
""",
"""        await minigameHumanPause('settle',{module:'chests',lotId:target.lotId});
        const rewards=await dismissTreasureRewards(runId);
""",
"chest settle before rewards")
rep("""        dispatchAutoMapTap(button,'chest-reward-'+(i+1));
        clicked+=1;
        await new Promise(resolve=>setTimeout(resolve,280));
""",
"""        await minigameHumanPause('reward',{module:'chests',index:i+1});
        dispatchAutoMapTap(button,'chest-reward-'+(i+1));
        clicked+=1;
        await minigameHumanPause('settle',{module:'chest-reward',index:i+1});
""",
"chest rewards")
rep("""        if (runId===chestAutoRunId) chestAutoRunning=false;
        lastSignature='';
        setTimeout(checkPuzzle,320);
""",
"""        if (runId===chestAutoRunId) chestAutoRunning=false;
        lastSignature='';
        setTimeout(checkPuzzle,minigameRandomMs(1400,2200));
""",
"chest next")

# AutoMap card and confirmation also get deliberate delays; backoffs become long
# enough that 429/409 are never followed by an immediate retry.
rep("""      const wait=status===409 ? 1800 :
        status===429 ? 3600 :
        status>=500 ? 5600 : 2200;
""",
"""      const wait=status===409 ? minigameRandomMs(5000,8000) :
        status===429 ? minigameRandomMs(14000,19000) :
        status>=500 ? minigameRandomMs(8000,12000) : minigameRandomMs(3500,5500);
""",
"automap backoff")
rep("""      autoMapActionCount+=1;
      autoMapLastActionAt=Date.now();

      if (!dispatchAutoMapTap(element,'auto-map-'+label)) {
""",
"""      autoMapActionCount+=1;
      await minigameHumanPause('map',{module:'auto-map',label});
      if (runId!==autoMapRunId || !autoMapEnabled()) return false;
      autoMapLastActionAt=Date.now();

      if (!dispatchAutoMapTap(element,'auto-map-'+label)) {
""",
"automap target pause")
rep("""      autoMapLastActionAt=Date.now();
      if (!dispatchAutoMapTap(action,'auto-map-confirm-'+label)) {
""",
"""      await minigameHumanPause('confirm',{module:'auto-map',label});
      if (runId!==autoMapRunId || !autoMapEnabled()) return false;
      autoMapLastActionAt=Date.now();
      if (!dispatchAutoMapTap(action,'auto-map-confirm-'+label)) {
""",
"automap confirm pause")
rep("""        if (autoMapStateFingerprint()!==before) {
          await new Promise(resolve=>setTimeout(resolve,260));
          return true;
        }
""",
"""        if (autoMapStateFingerprint()!==before) {
          await minigameHumanPause('settle',{module:'auto-map',label});
          return true;
        }
""",
"automap settle")

rep("      fishingBudgetRevision:HK_FISHING_BUDGET_REV,\n      start,",
    "      fishingBudgetRevision:HK_FISHING_BUDGET_REV,\n      minigameHumanPacingRevision:HK_MINIGAME_HUMAN_PACING_REV,\n      start,",
    "export revision")

for marker in [
    "// @version      1.18.26",
    "const BUILD_VERSION = '1.18.26';",
    "minigame-human-pacing-20260927-r1",
    "async function minigameHumanPause",
    "status===429",
    "minigameRandomMs(14000,19000)",
    "await minigameHumanPause('scan',{module:'trader'})",
    "await minigameHumanPause('confirm',{module:'fishing'",
    "await minigameHumanPause('scan',{module:'chests'})",
    "AUTO_MAP_ACTION_GAP_MS=2400",
    "trader-approved-lots-20260927-r1",
    "fishing-live-budget-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("MINIGAME_HUMAN_PACING_1_18_26=PASS")
