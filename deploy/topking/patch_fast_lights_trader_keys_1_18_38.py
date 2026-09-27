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

rep(
"// @release-note Автокарта/Лабиринт: после основной награды выход выполняется через широкую нижнюю кнопку стоимости 10, а не через маленькую квадратную кнопку слева — она открывает инструкцию. Кнопка 10 теперь ищется по точной геометрии нижнего футера и подтверждается как обычная покупка выхода; инструкция больше не используется как fallback.",
"// @release-note Автокарта/Лабиринт: выход после основной награды — через широкую кнопку 10, маленькая кнопка инструкции исключена. Лампочки подтверждаются быстрее: один клик 1, короткое ожидание ответа, закрытие модалки и проверка поля без повторной покупки. Торговец работает быстрее с защитой от 429 и теперь покупает также ключи common/uncommon/rare/epic/legendary.",
"release note")

rep(
"  const HK_LIGHTS_COST_EXIT_REV = 'lights-cost10-exit-20260927-r1';",
"  const HK_LIGHTS_COST_EXIT_REV = 'lights-cost10-exit-20260927-r1';\n  const HK_LIGHTS_FAST_CONFIRM_REV = 'lights-fast-confirm-20260927-r1';\n  const HK_TRADER_KEYS_FAST_REV = 'trader-keys-fast-20260927-r1';",
"revisions")

rep("    const LIGHTS_AUTO_SETTLE_MS = 1600;",
    "    const LIGHTS_AUTO_SETTLE_MS = 450;",
    "lights settle")
rep("    const LIGHTS_AUTO_CHANGE_TIMEOUT_MS = 4200;",
    "    const LIGHTS_AUTO_CHANGE_TIMEOUT_MS = 3200;",
    "lights change timeout")
rep("    const TRADER_ACTION_TIMEOUT_MS = 5200;",
    "    const TRADER_ACTION_TIMEOUT_MS = 3600;",
    "trader action timeout")
rep("    const TRADER_MIN_NEXT_ACTION_GAP_MS = 2800;",
    "    const TRADER_MIN_NEXT_ACTION_GAP_MS = 1200;",
    "trader action gap")

rep(
"""      // Treasure coins. "4coins" alone is NOT enough: key_uncommon4coins is a key.
      if (/random4coins/.test(id) || /treasure[_-]?coins/.test(id)) return true;

      // Berries/food lots.
""",
"""      // Treasure coins.
      if (/random4coins/.test(id) || /treasure[_-]?coins/.test(id)) return true;

      // Keys are explicitly approved too (common/uncommon/rare/epic/legendary).
      if (/key_(?:common|uncommon|rare|epic|legendary)4coins/.test(id)) return true;

      // Berries/food lots.
""",
"approve trader keys")

rep(
"""    function traderValueTier(lotId) {
      const id=String(lotId||'').toLowerCase();
      if (/map/.test(id)) return 1200;
      if (/coins/.test(id)) return 1100;
      if (/food|berry|berries|energy/.test(id)) return 1000;
""",
"""    function traderValueTier(lotId) {
      const id=String(lotId||'').toLowerCase();
      if (/key_(?:common|uncommon|rare|epic|legendary)4coins/.test(id)) return 1250;
      if (/map/.test(id)) return 1200;
      if (/coins/.test(id)) return 1100;
      if (/food|berry|berries|energy/.test(id)) return 1000;
""",
"key trader tier")

anchor="""    async function fishingHumanPause(stage='scan',data={}) {
"""
helper="""    async function traderHumanPause(stage='scan',data={}) {
      const ranges={
        scan:[250,450],
        aim:[180,320],
        confirm:[300,520],
        settle:[450,700],
        reward:[260,440]
      };
      const range=ranges[stage] || ranges.scan;
      const waitMs=minigameRandomMs(range[0],range[1]);
      recordDiagnostic('trader-human-pause',{
        revision:HK_TRADER_KEYS_FAST_REV,
        stage,
        waitMs,
        ...data
      });
      await new Promise(resolve=>setTimeout(resolve,waitMs));
      return waitMs;
    }

"""
if s.count(anchor)!=1:
    raise SystemExit("fishingHumanPause anchor missing")
s=s.replace(anchor,helper+anchor,1)

for old,new,label in [
    ("      await minigameHumanPause('scan',{module:'trader'});",
     "      await traderHumanPause('scan',{module:'trader'});",
     "trader scan pause"),
    ("        await minigameHumanPause('aim',{module:'trader',lotId:target.lotId});",
     "        await traderHumanPause('aim',{module:'trader',lotId:target.lotId});",
     "trader aim pause"),
    ("        await minigameHumanPause('confirm',{module:'trader',lotId:target.lotId});",
     "        await traderHumanPause('confirm',{module:'trader',lotId:target.lotId});",
     "trader confirm pause"),
    ("        await minigameHumanPause('settle',{module:'trader',lotId:target.lotId});",
     "        await traderHumanPause('settle',{module:'trader',lotId:target.lotId});",
     "trader settle pause"),
]:
    rep(old,new,label)

rep("        while (Date.now()-directStarted<750) {",
    "        while (Date.now()-directStarted<420) {",
    "trader direct window")
rep("          while (Date.now()-started<2400) {",
    "          while (Date.now()-started<1200) {",
    "trader modal window")
rep("          await new Promise(resolve=>setTimeout(resolve,2200));",
    "          await new Promise(resolve=>setTimeout(resolve,900));",
    "trader modal reconcile")
rep("          while (Date.now()-started<2000) {",
    "          while (Date.now()-started<900) {",
    "trader action button window")
rep("          await new Promise(resolve=>setTimeout(resolve,2600));",
    "          await new Promise(resolve=>setTimeout(resolve,1200));",
    "trader field reconcile")

rep(
"    async function waitLightsStableBoard(runId,timeoutMs=2600,stableMs=360) {",
"    async function waitLightsStableBoard(runId,timeoutMs=1600,stableMs=180) {",
"lights stable window")

rep(
"""    async function waitLightsBoardChange(before,runId) {
      const started=Date.now();
      while (Date.now()-started<LIGHTS_AUTO_CHANGE_TIMEOUT_MS) {
""",
"""    async function waitLightsBoardChange(before,runId,timeoutMs=LIGHTS_AUTO_CHANGE_TIMEOUT_MS) {
      const started=Date.now();
      while (Date.now()-started<timeoutMs) {
""",
"lights board change timeout arg")

old_flow="""      // First wait only for the board itself to change. Do not return to the
      // planner while any lamp modal is still open.
      const changed=await waitLightsBoardChange(before,runId);
      if (!changed) return {ok:false,reason:'field-no-change'};

      const drained=await closeLightsModalAfterStateChange(runId,before,slot);
      if (!drained) {
        return {ok:false,reason:'modal-not-closed-after-change'};
      }

      recordDiagnostic('lights-auto-step-ui-complete',{
        revision:HK_LIGHTS_MODAL_STEP_REV,
        slot,
        mode:confirmMode,
        state:lightsBoardSignature()
      });
      return {ok:true,reason:'field-changed-modal-closed'};
"""
new_flow="""      // Fast path: the purchase is sent only once. For ~0.8s watch for either
      // an immediate field mutation or an acknowledgement/close affordance.
      // If the game keeps the purchase modal open, close that modal (never press
      // the cost button again) and then wait for the already-sent purchase to
      // settle on the 3x3 board.
      let changed=lightsBoardSignature()!==before;
      const fastStarted=Date.now();
      let fastCloseSent=false;

      while (!changed && Date.now()-fastStarted<820) {
        if (runId!==lightsAutoRunId || !lightsAutoEnabled()) {
          return {ok:false,reason:'cancelled'};
        }

        changed=lightsBoardSignature()!==before;
        if (changed) break;

        const current=lightsModalRoot();
        if (!current) {
          await new Promise(resolve=>setTimeout(resolve,70));
          continue;
        }

        const ack=lightsAcknowledgeButton(current);
        if (ack) {
          if (dispatchBattleTap(ack,'lights-fast-ack-'+slot)) {
            fastCloseSent=true;
            recordDiagnostic('lights-fast-confirm-ui',{
              revision:HK_LIGHTS_FAST_CONFIRM_REV,
              slot,
              action:'ack'
            });
            await new Promise(resolve=>setTimeout(resolve,150));
            break;
          }
        }

        await new Promise(resolve=>setTimeout(resolve,70));
      }

      changed=changed || lightsBoardSignature()!==before;

      if (!changed && !fastCloseSent) {
        const current=lightsModalRoot();
        if (current) {
          const close=lightsModalCloseButton(current);
          if (close && dispatchBattleTap(close,'lights-fast-close-'+slot)) {
            fastCloseSent=true;
            recordDiagnostic('lights-fast-confirm-ui',{
              revision:HK_LIGHTS_FAST_CONFIRM_REV,
              slot,
              action:'close'
            });
          } else {
            const rr=current.getBoundingClientRect?.();
            if (rr && rr.width>120 && rr.height>120) {
              fastCloseSent=dispatchBattleTapAt(
                rr.left+rr.width-18,
                rr.top+18,
                'lights-fast-close-corner-'+slot
              );
              if (fastCloseSent) {
                recordDiagnostic('lights-fast-confirm-ui',{
                  revision:HK_LIGHTS_FAST_CONFIRM_REV,
                  slot,
                  action:'corner'
                });
              }
            }
          }
          if (fastCloseSent) await new Promise(resolve=>setTimeout(resolve,180));
        }
      }

      if (!changed) {
        changed=await waitLightsBoardChange(before,runId,2600);
      }
      if (!changed) return {ok:false,reason:'field-no-change'};

      if (lightsModalRoot()) {
        const drained=await closeLightsModalAfterStateChange(runId,before,slot,1100);
        if (!drained) {
          return {ok:false,reason:'modal-not-closed-after-change'};
        }
      }

      recordDiagnostic('lights-auto-step-ui-complete',{
        revision:HK_LIGHTS_FAST_CONFIRM_REV,
        slot,
        mode:confirmMode,
        fastCloseSent,
        state:lightsBoardSignature()
      });
      return {ok:true,reason:'field-changed-modal-closed-fast'};
"""
rep(old_flow,new_flow,"fast lights confirm flow")

rep(
"      lightsCostExitRevision:HK_LIGHTS_COST_EXIT_REV,\n      start,",
"      lightsCostExitRevision:HK_LIGHTS_COST_EXIT_REV,\n      lightsFastConfirmRevision:HK_LIGHTS_FAST_CONFIRM_REV,\n      traderKeysFastRevision:HK_TRADER_KEYS_FAST_REV,\n      start,",
"export fast revisions")

for marker in [
    "lights-fast-confirm-20260927-r1",
    "trader-keys-fast-20260927-r1",
    "function traderHumanPause",
    "key_(?:common|uncommon|rare|epic|legendary)4coins",
    "TRADER_MIN_NEXT_ACTION_GAP_MS = 1200",
    "LIGHTS_AUTO_SETTLE_MS = 450",
    "field-changed-modal-closed-fast",
    "lights-fast-confirm-ui",
    "lights-cost10-exit-20260927-r1",
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("FAST_LIGHTS_TRADER_KEYS_1_18_38=PASS")

# trigger build after workflow installation
