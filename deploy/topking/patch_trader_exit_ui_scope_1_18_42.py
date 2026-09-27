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

rep("// @version      1.18.41",
    "// @version      1.18.42\n// @release-note Тайный торговец/Карта сокровищ: после выкупа всех разрешённых лотов Автокарта сразу передаёт управление выходу из комнаты и нажимает широкую нижнюю кнопку 10, затем продолжает маршрут. Поиск нижней кнопки исправлен для мобильной ширины. После выхода из события кнопки «Автокарта» и «Запись карты» скрываются вне экранов Карты сокровищ/её мини-игр, даже если режимы остаются включёнными.",
    "version")
rep("const BUILD_VERSION = '1.18.41';",
    "const BUILD_VERSION = '1.18.42';",
    "build")

rep(
"  const HK_TRADER_APPROVED_MODAL_REV = 'trader-approved-modal-buy-20260927-r1';",
"  const HK_TRADER_APPROVED_MODAL_REV = 'trader-approved-modal-buy-20260927-r1';\n  const HK_TRADER_EXIT_HANDOFF_REV = 'trader-exit-handoff-20260927-r1';\n  const HK_TREASURE_EVENT_UI_SCOPE_REV = 'treasure-event-ui-scope-20260927-r1';",
"revisions")

# Shared event context for UI visibility. Keep recorder/AutoMap buttons out of unrelated game screens.
anchor="""  function treasureGuideScreenVisible() {
    const text=String(document.body?.innerText||'');
    return /Карта\\s+Сокровищ|Treasure\\s+Map|نقشه\\s+گنج/i.test(text);
  }
"""
insert="""  function treasureEventContextVisible() {
    if (treasureGuideScreenVisible()) return true;
    try {
      const selectors=[
        '[data-lot-id^="mf_fairlot_minigame_trader_"]',
        '[data-lot-id^="mf_fairlot_lights_out_sl"]',
        '[data-lot-id*="mf_treasurelot_is_fishing_"]',
        '[data-lot-id*="mf_treasurelot_chest_"]',
        '[data-lot-id*="mf_treasurelot_enemy_type_"]',
        '[data-lot-id^="mf_treasurelot_sword_"]',
        '[data-lot-id*="mf_fairlot_minigame_treasury_room_big_chest"]',
        '[data-lot-id^="mf_fair_treasury_room_choose_way_"]'
      ];
      return selectors.some(selector=>[...document.querySelectorAll(selector)].some(visible));
    } catch (_) {
      return false;
    }
  }
"""
if s.count(anchor)!=1:
    raise SystemExit("treasureGuideScreenVisible anchor missing")
s=s.replace(anchor,anchor+"\n"+insert,1)

# Recorder button is visual UI only: hide outside the event, even if recording state remains ON.
rep(
"""    const active=treasureRunRecorderActive();
    const show=active || treasureGuideScreenVisible();
""",
"""    const active=treasureRunRecorderActive();
    const show=treasureEventContextVisible();
""",
"recorder UI scope")

# AutoMap button same rule: setting can stay ON but unrelated screens stay clean.
rep(
"""      const enabled=autoMapEnabled();
      const show=showOverride===null
        ? (enabled || treasureGuideScreenVisible())
        : !!showOverride;
""",
"""      const enabled=autoMapEnabled();
      const show=showOverride===null
        ? treasureEventContextVisible()
        : (!!showOverride && treasureEventContextVisible());
""",
"automap UI scope")

# Mobile footer button: the real yellow cost-10 action is wide (~75-85% viewport).
# Small square instruction/back control remains excluded by minimum width and center scoring.
old_geom="""          if (cy>=vh*0.84) score+=260;
          if (Math.abs(cx-centerX)<=vw*0.22) score+=220;
          if (rect.width>=vw*0.12 && rect.width<=vw*0.48) score+=220;
          if (rect.height>=30 && rect.height<=110) score+=100;
          if (actionable) score+=120;

          if (rect.width<vw*0.08) score-=700;
          if (rect.width>vw*0.60) score-=500;
          if (cx<=vw*0.28 || cx>=vw*0.78) score-=320;
"""
new_geom="""          if (cy>=vh*0.78) score+=260;
          if (Math.abs(cx-centerX)<=vw*0.18) score+=240;
          if (rect.width>=vw*0.26 && rect.width<=vw*0.92) score+=260;
          if (rect.height>=30 && rect.height<=120) score+=100;
          if (actionable) score+=120;

          if (rect.width<vw*0.20) score-=900;
          if (rect.width>vw*0.96) score-=500;
          if (cx<=vw*0.25 || cx>=vw*0.75) score-=420;
"""
rep(old_geom,new_geom,"mobile bottom cost button geometry")

# Dedicated trader-complete handoff helper. It only exits once no approved target/modal remains.
anchor="""    function traderBackoff(reason,data={}) {
      const error=minigameRecentHttpError(data?.startedAt||0);
"""
helper="""    function traderRoomComplete() {
      const signature=getSignature();
      if (!signature.startsWith('TRADER|')) return false;
      if (traderApprovedOpenModal()) return false;
      return !traderTarget();
    }

    function traderScheduleExitHandoff(reason='trader-complete') {
      if (!autoMapEnabled()) return false;
      if (!traderRoomComplete()) return false;
      traderRetryNotBefore=0;
      lastSignature='';
      recordDiagnostic('trader-exit-handoff',{
        revision:HK_TRADER_EXIT_HANDOFF_REV,
        reason,
        purchases:traderSessionPurchases
      });
      setTimeout(()=>void runAutoMapTick('trader-exit-handoff-'+reason),120);
      return true;
    }

"""
if s.count(anchor)!=1:
    raise SystemExit("traderBackoff anchor missing")
s=s.replace(anchor,helper+anchor,1)

# When there are no more approved affordable lots, do not just stop trader.
old_no_target="""      let target=traderTarget();
      if (!target) {
        const visible=traderElements().filter(row=>!row.activated);
        recordDiagnostic('trader-auto-complete',{
          revision:HK_TRADER_WHITELIST_REV,
          purchases:traderSessionPurchases,
          reason:'no-approved-affordable-lots',
          skipped:visible.filter(row=>!traderApprovedRow(row)).map(row=>row.lotId).slice(0,24)
        });
        return false;
      }
"""
new_no_target="""      let target=traderTarget();
      if (!target) {
        const visible=traderElements().filter(row=>!row.activated);
        recordDiagnostic('trader-auto-complete',{
          revision:HK_TRADER_EXIT_HANDOFF_REV,
          purchases:traderSessionPurchases,
          reason:'no-approved-affordable-lots',
          skipped:visible.filter(row=>!traderApprovedRow(row)).map(row=>row.lotId).slice(0,24)
        });
        traderScheduleExitHandoff('no-approved-target');
        return false;
      }
"""
rep(old_no_target,new_no_target,"trader no target exit handoff")

# After each successful purchase, if that was the last approved lot, hand off immediately.
old_purchase_tail="""        recordDiagnostic('trader-auto-purchase',{
          revision:HK_TRADER_AUTO_REV,
          lotId:target.lotId,
          cost:target.cost.parts,
          rewardsDismissed:rewards,
          purchases:traderSessionPurchases
        });
        return true;
"""
new_purchase_tail="""        recordDiagnostic('trader-auto-purchase',{
          revision:HK_TRADER_AUTO_REV,
          lotId:target.lotId,
          cost:target.cost.parts,
          rewardsDismissed:rewards,
          purchases:traderSessionPurchases
        });
        traderScheduleExitHandoff('purchase-complete');
        return true;
"""
rep(old_purchase_tail,new_purchase_tail,"trader purchase exit handoff")

# Direct-purchase success path too.
old_direct="""            recordDiagnostic('trader-auto-purchase',{
              revision:HK_TRADER_AUTO_REV,
              lotId:target.lotId,
              mode:'direct',
              purchases:traderSessionPurchases
            });
            return true;
"""
new_direct="""            recordDiagnostic('trader-auto-purchase',{
              revision:HK_TRADER_AUTO_REV,
              lotId:target.lotId,
              mode:'direct',
              purchases:traderSessionPurchases
            });
            traderScheduleExitHandoff('direct-purchase-complete');
            return true;
"""
rep(old_direct,new_direct,"trader direct exit handoff")

# AutoMap trader branch: use explicit trader completion status and direct footer handoff.
old_branch="""        if (signature.startsWith('TRADER|')) {
          autoMapStatus('торговец');
          if (traderTarget()) {
            lastSignature='';
            setTimeout(checkPuzzle,20);
          } else {
            await autoMapHandleExitOrContinue();
          }
          return true;
        }
"""
new_branch="""        if (signature.startsWith('TRADER|')) {
          if (traderTarget() || traderApprovedOpenModal()) {
            autoMapStatus('торговец');
            lastSignature='';
            setTimeout(checkPuzzle,20);
          } else {
            autoMapStatus('торговец → выход',{
              revision:HK_TRADER_EXIT_HANDOFF_REV
            });
            const left=await autoMapHandleExitOrContinue();
            if (!left) {
              autoMapRetryNotBefore=Date.now()+650;
              setTimeout(()=>void runAutoMapTick('trader-exit-retry'),760);
            }
          }
          return true;
        }
"""
rep(old_branch,new_branch,"trader automap direct exit branch")

rep(
"      traderApprovedModalRevision:HK_TRADER_APPROVED_MODAL_REV,\n      start,",
"      traderApprovedModalRevision:HK_TRADER_APPROVED_MODAL_REV,\n      traderExitHandoffRevision:HK_TRADER_EXIT_HANDOFF_REV,\n      treasureEventUiScopeRevision:HK_TREASURE_EVENT_UI_SCOPE_REV,\n      start,",
"export revisions")

for marker in [
    "// @version      1.18.42",
    "const BUILD_VERSION = '1.18.42';",
    "trader-exit-handoff-20260927-r1",
    "treasure-event-ui-scope-20260927-r1",
    "function treasureEventContextVisible()",
    "const show=treasureEventContextVisible();",
    "traderScheduleExitHandoff('no-approved-target')",
    "торговец → выход",
    "rect.width>=vw*0.26 && rect.width<=vw*0.92",
    "treasury-visual-exit-20260927-r2",
    "trader-approved-modal-buy-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TRADER_EXIT_UI_SCOPE_1_18_42=PASS")
