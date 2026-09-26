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

rep("// @version      1.18.20",
    "// @version      1.18.21\n// @release-note Автокарта: исправлен переход мини-игра → карта. Пока бой/рыбалка/торговец/лампочки/сундуки реально находятся на переднем плане, клетки карты под ними не нажимаются. Автокарта больше не выходит из боя до его полного завершения. После возврата на карту действует короткий settle-lock. Двойные клики покупок в сундуках/рыбалке/торговце заменены одиночными.",
    "version")
rep("const BUILD_VERSION = '1.18.20';",
    "const BUILD_VERSION = '1.18.21';",
    "build")
rep("  const HK_TREASURE_AUTO_MAP_ACTIVE_PRIORITY_REV='treasure-auto-map-active-priority-20260926-r5';",
    "  const HK_TREASURE_AUTO_MAP_ACTIVE_PRIORITY_REV='treasure-auto-map-active-priority-20260926-r5';\n  const HK_TREASURE_AUTO_MAP_HANDOFF_REV='treasure-auto-map-foreground-handoff-20260926-r6';",
    "revision")

rep("    const AUTO_MAP_NO_ACTIVE_COMPLETE_MS=4500;\n    const AUTO_MAP_LOOP_MS=420;",
    "    const AUTO_MAP_NO_ACTIVE_COMPLETE_MS=4500;\n    const AUTO_MAP_RETURN_SETTLE_MS=1600;\n    const AUTO_MAP_LOOP_MS=420;",
    "settle constant")
rep("    let autoMapNoActiveSince=0;",
    "    let autoMapNoActiveSince=0;\n    let autoMapReturnNotBefore=0;",
    "settle state")

anchor="    function autoMapJourneyButton() {"
if s.count(anchor)!=1:
    raise SystemExit("journey anchor")
helpers="""    function autoMapMiniGameForeground() {
      const signature=getSignature();
      return /^(?:LIGHTS|BATTLE|FISHING|TRADER|CHESTS)(?:\\||$|_)/.test(signature);
    }

    function autoMapModalCloseButton(root) {
      if (!root) return null;
      const candidates=[...root.querySelectorAll('button,[role="button"],a,div,span')]
        .filter(el=>el && el!==autoMapToggle && !el.disabled && visible(el))
        .map(el=>{
          const text=clean(el.innerText||el.textContent||'').trim();
          const aria=clean(el.getAttribute?.('aria-label')||'').trim();
          const rect=el.getBoundingClientRect?.() || {width:0,height:0,left:0,top:0};
          let score=0;
          if (/^(?:×|✕|Назад|Back|Закрыть|Close)$/i.test(text)) score+=180;
          if (/close|закрыть|back|назад/i.test(aria)) score+=160;
          if (rect.width>0 && rect.width<=90 && rect.height>0 && rect.height<=90) score+=25;
          return {el,score,area:rect.width*rect.height};
        })
        .filter(row=>row.score>=160)
        .sort((a,b)=>b.score-a.score || a.area-b.area);
      return candidates[0]?.el || null;
    }

    async function autoMapCloseLingeringModal(reason='stale-modal') {
      if (autoMapMiniGameForeground()) return false;
      const root=treasureModalRoot(null);
      if (!root) return false;
      const close=autoMapModalCloseButton(root);
      if (!close) {
        autoMapStatus('жду окно',{reason});
        return false;
      }
      dispatchAutoMapTap(close,'close-'+reason);
      autoMapLastActionAt=Date.now();
      recordDiagnostic('treasure-auto-map-modal-close',{
        revision:HK_TREASURE_AUTO_MAP_HANDOFF_REV,
        reason
      });
      await new Promise(resolve=>setTimeout(resolve,420));
      return true;
    }

"""
s=s.replace(anchor,helpers+anchor,1)

rep("""      if (autoMapModulesRunning()) {
        autoMapStatus('мини-игра');
        return false;
      }
""",
"""      if (autoMapModulesRunning()) {
        autoMapReturnNotBefore=Date.now()+AUTO_MAP_RETURN_SETTLE_MS;
        autoMapStatus('мини-игра');
        return false;
      }
""",
"module running return lock")

reward_block="""        if (treasureRewardButton()) {
          await autoMapDismissReward();
          lastSignature='';
          setTimeout(checkPuzzle,80);
          return true;
        }
"""
if s.count(reward_block)!=1:
    raise SystemExit("reward block missing")
after_reward=reward_block+"""
        const foregroundNow=autoMapMiniGameForeground();
        if (foregroundNow) {
          autoMapReturnNotBefore=Date.now()+AUTO_MAP_RETURN_SETTLE_MS;
        } else if (treasureGuideScreenVisible() && Date.now()<autoMapReturnNotBefore) {
          autoMapStatus('возврат на карту',{
            waitMs:autoMapReturnNotBefore-Date.now()
          });
          return false;
        }

        // A stale purchase/confirmation modal from a failed 409 must be closed
        // before the next map cell can be considered.
        if (!foregroundNow && treasureGuideScreenVisible() && treasureModalRoot(null)) {
          const closed=await autoMapCloseLingeringModal('map-overlay');
          if (closed) return true;
          return false;
        }
"""
s=s.replace(reward_block,after_reward,1)

# Gate both current-map blocks so underlying cells are never used through a minigame.
rep("        if (treasureGuideScreenVisible()) {\n          const activeCount=autoMapActiveCellCount();",
    "        if (!autoMapMiniGameForeground() && !treasureModalRoot(null) && Date.now()>=autoMapReturnNotBefore && treasureGuideScreenVisible()) {\n          const activeCount=autoMapActiveCellCount();",
    "active map foreground gate")
rep("        if (treasureGuideScreenVisible() && autoMapJourneyButton()) {",
    "        if (!autoMapMiniGameForeground() && !treasureModalRoot(null) && Date.now()>=autoMapReturnNotBefore && treasureGuideScreenVisible() && autoMapJourneyButton()) {",
    "journey foreground gate")
rep("        if (treasureGuideScreenVisible()) {\n          const target=autoMapMapCards()[0];",
    "        if (!autoMapMiniGameForeground() && !treasureModalRoot(null) && Date.now()>=autoMapReturnNotBefore && treasureGuideScreenVisible()) {\n          const target=autoMapMapCards()[0];",
    "legacy map foreground gate")

# Active battle can show "Покинуть локацию" all the time; that does NOT mean complete.
rep("      if (signature.startsWith('BATTLE')) return !!autoMapExitButton();",
    "      if (signature.startsWith('BATTLE')) return false;",
    "battle completion guard")
rep("""    async function autoMapHandleExitOrContinue() {
      if (autoMapModulesRunning()) return false;
      const exit=autoMapExitButton();
""",
"""    async function autoMapHandleExitOrContinue() {
      if (autoMapModulesRunning()) return false;
      const signature=getSignature();
      if (signature.startsWith('BATTLE')) return false;
      const exit=autoMapExitButton();
""",
"battle exit safety")

old_battle="""        if (signature.startsWith('BATTLE')) {
          autoMapStatus('сражение');
          if (signature.startsWith('BATTLE_REWARD') && battleAutoEnabled()) {
            lastSignature='';
            setTimeout(checkPuzzle,20);
          } else if (autoMapExitButton()) {
            await autoMapHandleExitOrContinue();
          } else {
            lastSignature='';
            setTimeout(checkPuzzle,20);
          }
          return true;
        }
"""
new_battle="""        if (signature.startsWith('BATTLE')) {
          // Battle module owns the whole battle until victory/reward state is gone.
          // Never press the persistent "Покинуть локацию" while enemies remain.
          autoMapReturnNotBefore=Date.now()+AUTO_MAP_RETURN_SETTLE_MS;
          autoMapStatus('сражение');
          lastSignature='';
          setTimeout(checkPuzzle,20);
          return true;
        }
"""
rep(old_battle,new_battle,"battle ownership")

# Clear handoff state on toggle.
rep("      autoMapNoActiveSince=0;\n      if (!value) autoMapSkipLotsUntil.clear();",
    "      autoMapNoActiveSince=0;\n      autoMapReturnNotBefore=0;\n      if (!value) autoMapSkipLotsUntil.clear();",
    "reset handoff state")

# Single-click the economic mini-game actions. The old battle compatibility tap
# emits a synthetic click plus .click(), which produced duplicate /shop/buy requests.
rep("        dispatchBattleTap(button,'chest-reward-'+(i+1));",
    "        dispatchAutoMapTap(button,'chest-reward-'+(i+1));",
    "chest reward single")
rep("        dispatchBattleTap(target.element,target.digging?'chest-dig-spot':'chest-open-card');",
    "        dispatchAutoMapTap(target.element,target.digging?'chest-dig-spot':'chest-open-card');",
    "chest open single")
rep("        if (action) tapped=dispatchBattleTap(action,target.digging?'chest-dig-confirm':'chest-open-confirm');",
    "        if (action) tapped=dispatchAutoMapTap(action,target.digging?'chest-dig-confirm':'chest-open-confirm');",
    "chest confirm single")
rep("        if (!dispatchBattleTap(target.element,'fishing-open-'+target.lotId)) {",
    "        if (!dispatchAutoMapTap(target.element,'fishing-open-'+target.lotId)) {",
    "fishing open single")
rep("        if (!action || !dispatchBattleTap(action,'fishing-confirm-'+target.lotId)) {",
    "        if (!action || !dispatchAutoMapTap(action,'fishing-confirm-'+target.lotId)) {",
    "fishing confirm single")
rep("        if (!dispatchBattleTap(target.element,'trader-open-'+target.lotId)) {",
    "        if (!dispatchAutoMapTap(target.element,'trader-open-'+target.lotId)) {",
    "trader open single")
rep("        if (!action || !dispatchBattleTap(action,'trader-confirm-'+target.lotId)) {",
    "        if (!action || !dispatchAutoMapTap(action,'trader-confirm-'+target.lotId)) {",
    "trader confirm single")
rep("        if (!dispatchBattleTap(button,'fishing-reward-'+(i+1))) break;",
    "        if (!dispatchAutoMapTap(button,'fishing-reward-'+(i+1))) break;",
    "fishing reward single")

rep("      treasureAutoMapActivePriorityRevision:HK_TREASURE_AUTO_MAP_ACTIVE_PRIORITY_REV,\n      start,",
    "      treasureAutoMapActivePriorityRevision:HK_TREASURE_AUTO_MAP_ACTIVE_PRIORITY_REV,\n      treasureAutoMapHandoffRevision:HK_TREASURE_AUTO_MAP_HANDOFF_REV,\n      start,",
    "export revision")

for marker in [
    "// @version      1.18.21",
    "const BUILD_VERSION = '1.18.21';",
    "treasure-auto-map-foreground-handoff-20260926-r6",
    "AUTO_MAP_RETURN_SETTLE_MS=1600",
    "function autoMapMiniGameForeground()",
    "Never press the persistent",
    "signature.startsWith('BATTLE')) return false",
    "dispatchAutoMapTap(target.element,target.digging?'chest-dig-spot':'chest-open-card')",
    "dispatchAutoMapTap(target.element,'fishing-open-'+target.lotId)",
    "dispatchAutoMapTap(target.element,'trader-open-'+target.lotId)",
    "treasure-auto-map-active-priority-20260926-r5"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_AUTO_MAP_HANDOFF_1_18_21=PASS")
