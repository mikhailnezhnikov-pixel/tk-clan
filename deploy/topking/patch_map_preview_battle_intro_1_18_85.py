from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count:
        raise SystemExit(f"{label}: expected {count}, got {n}")
    s=s.replace(old,new,count)

rep("// @version      1.18.84",
    "// @version      1.18.85\n// @release-note Автокарта: убрано ложное «закрываю Золотые монеты» на превью локаций. Сражение: «Понятно/OK» теперь жёстко блокирует выход до загрузки поля.",
    "version")
rep("const BUILD_VERSION = '1.18.84';","const BUILD_VERSION = '1.18.85';","build")
rep("  const HK_TRADER_GOLD_STALE_MODAL_REV='trader-gold-stale-modal-reset-20260929-r1';",
    "  const HK_TRADER_GOLD_STALE_MODAL_REV='trader-gold-stale-modal-reset-20260929-r1';\n  const HK_TRADER_GOLD_EXACT_MODAL_REV='trader-gold-exact-purchase-modal-20260929-r1';",
    "gold rev")
rep("  const HK_BATTLE_VISIBLE_POINT_TRUTH_REV='battle-visible-point-truth-20260929-r1';",
    "  const HK_BATTLE_VISIBLE_POINT_TRUTH_REV='battle-visible-point-truth-20260929-r1';\n  const HK_BATTLE_INTRO_HARD_GATE_REV='battle-intro-hard-gate-20260929-r1';",
    "battle rev")
rep("    let battleAutoRunning=false;\n",
    "    let battleAutoRunning=false;\n    let battleIntroGateUntil=0;\n",
    "battle state")

# Keep the 1.18.83 detector only as a legacy fallback name; install a strict
# purchase-modal detector under the public function name.
rep("    function traderForbiddenGoldModalRoot() {",
    "    function traderForbiddenGoldModalRootLegacy() {",
    "rename gold detector")
gold_anchor="    function traderForbiddenGoldCloseButton(root=traderForbiddenGoldModalRoot()) {"
gold_fn=r'''    function traderForbiddenGoldModalRoot() {
      const title=/^(?:Золотые\s+монеты|Golden\s+Coins|Gold\s+Coins)$/i;
      const purchase=/(?:Покупка\s+повышает\s+репутацию\s+у\s+торговца|Purchase.{0,80}(?:reputation|standing).{0,80}(?:trader|merchant))/i;
      const rows=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"],div')]
        .filter(visible)
        .map(element=>{
          const rect=element.getBoundingClientRect?.();
          const raw=String(element.innerText||element.textContent||'');
          const lines=raw.split(/\n+/).map(v=>clean(v).trim()).filter(Boolean);
          return {
            element,
            rect,
            exactTitle:lines.some(line=>title.test(line)),
            purchaseText:purchase.test(clean(raw))
          };
        })
        .filter(row=>row.rect && row.rect.width>=Math.min(240,window.innerWidth*0.35) && row.rect.height>=180)
        .filter(row=>row.exactTitle && row.purchaseText)
        .sort((a,b)=>a.rect.width*a.rect.height-b.rect.width*b.rect.height);
      return rows[0]?.element || null;
    }

'''
if s.count(gold_anchor)!=1:
    raise SystemExit("gold close anchor missing")
s=s.replace(gold_anchor,gold_fn+gold_anchor,1)

# Replace the old intro detector with a legacy name and put a broader mobile-safe
# detector in front of its acknowledgement helper.
rep("    function battleIntroModalRoot() {",
    "    function battleIntroModalRootLegacy() {",
    "rename battle intro detector")
intro_anchor="    function battleIntroAcknowledgeButton(root=battleIntroModalRoot()) {"
intro_fn=r'''    function battleIntroModalRoot() {
      const direct=battleIntroModalRootLegacy();
      if (direct) {
        battleIntroGateUntil=Math.max(battleIntroGateUntil,Date.now()+5000);
        return direct;
      }

      const exactAck=/^(?:Понятно|Got it|Understood|OK|Okay)$/i;
      let battleContext=battleRawContextPresent();
      try { battleContext=battleContext || !!battleFairState(); } catch (_) {}
      if (!battleContext) return null;

      const rows=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"],[class*="modal"],[class*="popup"],[class*="dialog"],div')]
        .filter(visible)
        .map(element=>{
          const text=clean(element.innerText||element.textContent||'').trim();
          const ack=[...element.querySelectorAll('button,[role="button"],a,[onclick],div,span')]
            .find(child=>exactAck.test(clean(child.innerText||child.textContent||'').trim()) && visible(child));
          const rect=element.getBoundingClientRect?.() || {width:0,height:0};
          return {element,text,ack,rect,area:rect.width*rect.height};
        })
        .filter(row=>row.ack)
        .filter(row=>!/Сундук победителя|Victory chest|Winner chest|Ключ сокровищ|Treasure key|Золотые монеты|Golden Coins|Gold Coins/i.test(row.text))
        .filter(row=>row.rect.width>=Math.min(220,window.innerWidth*0.30) && row.rect.height>=100)
        .sort((a,b)=>a.area-b.area);

      const root=rows[0]?.element || null;
      if (root) battleIntroGateUntil=Math.max(battleIntroGateUntil,Date.now()+5000);
      return root;
    }

    function battleIntroTransitionLocked() {
      return Date.now()<battleIntroGateUntil;
    }

'''
if s.count(intro_anchor)!=1:
    raise SystemExit("intro ack anchor missing")
s=s.replace(intro_anchor,intro_fn+intro_anchor,1)

rep("    async function runBattleIntroAcknowledge() {\n      if (!battleAutoEnabled() || battleAutoRunning) return false;",
    "    async function runBattleIntroAcknowledge() {\n      if ((!battleAutoEnabled() && !autoMapEnabled()) || battleAutoRunning) return false;\n      if (autoMapEnabled() && !battleAutoEnabled()) setBattleAutoEnabled(true);",
    "intro ownership")

rep("          if (!battleIntroAcknowledgeButton()) {\n            lastSignature='';",
    "          if (!battleIntroAcknowledgeButton()) {\n            battleIntroGateUntil=Date.now()+2600;\n            lastSignature='';",
    "intro transition lock")

# Exit guards.
rep("      if (/(?:leave|exit)/i.test(String(label||''))) {\n        const battleGate=battleExitState();",
    "      if (/(?:leave|exit)/i.test(String(label||''))) {\n        if (battleIntroModalRoot() || battleIntroTransitionLocked()) { autoMapStatus('сражение → жду поле'); return false; }\n        const battleGate=battleExitState();",
    "tap-confirm exit gate")
rep("    function autoMapCurrentModuleComplete() {\n      const signature=getSignature();",
    "    function autoMapCurrentModuleComplete() {\n      if (battleIntroModalRoot() || battleIntroTransitionLocked()) return false;\n      const signature=getSignature();",
    "module complete gate")
rep("    async function autoMapHandleExitOrContinue() {\n      if (autoMapModulesRunning()) return false;",
    "    async function autoMapHandleExitOrContinue() {\n      if (autoMapModulesRunning()) return false;\n      if (battleIntroModalRoot() || battleIntroTransitionLocked()) { autoMapStatus('сражение → жду поле'); return false; }",
    "exit handoff gate")

# Intro gate must run before leave-modal recovery.
preflight_anchor="      // A leave-confirmation modal can survive a redraw/retry. It is always\n"
preflight=r'''      const introHardGate=battleIntroModalRoot();
      if (introHardGate) {
        if (!battleAutoEnabled()) setBattleAutoEnabled(true);
        if (!battleAutoRunning) {
          autoMapStatus('сражение → понятно',{revision:HK_BATTLE_INTRO_HARD_GATE_REV});
          return await runBattleIntroAcknowledge();
        }
        return false;
      }
      if (battleIntroTransitionLocked()) {
        const sig=getSignature();
        if (!sig.startsWith('BATTLE')) {
          autoMapStatus('сражение → загружаю поле',{revision:HK_BATTLE_INTRO_HARD_GATE_REV});
          setTimeout(()=>void runAutoMapTick('battle-intro-transition'),120);
          return false;
        }
        battleIntroGateUntil=0;
      }

'''
if s.count(preflight_anchor)!=1:
    raise SystemExit("preflight anchor missing")
s=s.replace(preflight_anchor,preflight+preflight_anchor,1)

rep("      traderGoldStaleModalRevision:HK_TRADER_GOLD_STALE_MODAL_REV,",
    "      traderGoldStaleModalRevision:HK_TRADER_GOLD_STALE_MODAL_REV,\n      traderGoldExactModalRevision:HK_TRADER_GOLD_EXACT_MODAL_REV,",
    "gold export")
rep("      battleVisiblePointTruthRevision:HK_BATTLE_VISIBLE_POINT_TRUTH_REV,",
    "      battleVisiblePointTruthRevision:HK_BATTLE_VISIBLE_POINT_TRUTH_REV,\n      battleIntroHardGateRevision:HK_BATTLE_INTRO_HARD_GATE_REV,",
    "battle export")

for marker in [
    "// @version      1.18.85",
    "trader-gold-exact-purchase-modal-20260929-r1",
    "battle-intro-hard-gate-20260929-r1",
    "function battleIntroTransitionLocked()",
    "battle-intro-transition",
    "row.exactTitle && row.purchaseText",
    "clan-crest-transparent-mask-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

p.write_text(s,encoding="utf-8")
print("MAP_PREVIEW_BATTLE_INTRO_1_18_85=PASS")
