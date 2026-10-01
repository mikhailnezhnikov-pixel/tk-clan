from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')

def rep(old,new,label,count=1):
    global s
    actual=s.count(old)
    if actual!=count:
        raise SystemExit(f'{label}: expected {count}, got {actual}')
    s=s.replace(old,new,count)

rep('// @version      1.18.99',
    '// @version      1.18.100\n// @release-note Сражения: исправлено распознавание стоимости 1–2 меча в открытой карточке бойца. Переключатели автокарты/автобоя больше не перекрывают кнопку атаки. Если нажатие отправлено, повторная оплата блокируется до фактического изменения игрового состояния.',
    'version')
rep("const BUILD_VERSION = '1.18.99';",
    "const BUILD_VERSION = '1.18.100';",'build version')
rev="  const HK_BATTLE_ATTACK_RECEIPT_REV='battle-attack-state-receipt-20261001-r1';"
rep(rev,rev+"\n  const HK_BATTLE_MOBILE_PRICE_REV='battle-mobile-price-action-20261001-r1';\n  const HK_BATTLE_SINGLE_TAP_REV='battle-single-tap-until-receipt-20261001-r1';",
    'new revisions')

# The 1.18.96 Python patch accidentally wrote *double* backslashes to a JS
# REGEX LITERAL. Unlike strings passed to RegExp(), a literal needs one slash.
# Both auto-discovery (expectedCost=null) and cost inference were always null.
rep(r'const numericMatch=text.match(/(?:^|\\s)(\\d{1,4})(?:\\s|$)/);',
    r'const numericMatch=text.match(/(?:^|\s)(\d{1,4})(?:\s|$)/);',
    'mobile numeric price regex')
rep(r'const values=[...text.matchAll(/(?:^|\\s)(\\d{1,4})(?=\\s|$)/g)]',
    r'const values=[...text.matchAll(/(?:^|\s)(\d{1,4})(?=\s|$)/g)]',
    'mobile price inference regex')
# The dynamically constructed RegExp strings are deliberately unchanged:
# their double slashes are correct JavaScript *string* escaping.

# Long green indicators occupied the middle/bottom of mobile modals.
rep("""      if (isBattle !== null) battleAutoToggle.style.display=isBattle ? 'block' : 'none';""",
"""      const enemyModalOpen=!!battleEnemyModalRoot();
      const battleHudTop=enemyModalOpen?'132px':'auto';
      const battleHudBottom=enemyModalOpen?'auto':'154px';
      if (battleAutoToggle.style.top!==battleHudTop) battleAutoToggle.style.top=battleHudTop;
      if (battleAutoToggle.style.bottom!==battleHudBottom) battleAutoToggle.style.bottom=battleHudBottom;
      if (isBattle !== null) battleAutoToggle.style.display=isBattle ? 'block' : 'none';""",
    'battle HUD moves above purchase area')
rep("""      const treasuryIntro=autoMapTreasuryIntroModalRoot();
      const hudBottom=treasuryIntro?'auto':'202px';
      const hudTop=treasuryIntro?'85px':'auto';""",
"""      const treasuryIntro=autoMapTreasuryIntroModalRoot();
      const enemyModalOpen=!!battleEnemyModalRoot();
      const hudBottom=(treasuryIntro||enemyModalOpen)?'auto':'202px';
      const hudTop=(treasuryIntro||enemyModalOpen)?'85px':'auto';""",
    'map HUD moves above purchase area')

# Purchase idempotence: pending only after a successful dispatch; unknown
# receipt must NOT trigger another attack of an unchanged fair board.
anchor="    async function battleConfirmAlreadyOpenEnemyModal(expectedCost,runId,beforeSignature=null) {"
rep(anchor,
"""    const battleAttackPending={
      key:'',sentAt:0
    };

"""+anchor,'pending ledger declaration')

rep("""      const beforeBoard=getBattleBoard().filter(Boolean)
        .map(enemy=>String(enemy.lotId||enemy.slot+':'+enemy.hp)).sort().join('|');
      let action=null,elapsed=Date.now();""",
"""      const beforeBoard=getBattleBoard().filter(Boolean)
        .map(enemy=>String(enemy.lotId||enemy.slot+':'+enemy.hp)).sort().join('|');
      const transactionKey=String(beforeSwords)+'|'+beforeBoard;
      if (battleAttackPending.key && battleAttackPending.key!==transactionKey) {
        battleAttackPending.key='';
        battleAttackPending.sentAt=0;
      }
      if (battleAttackPending.key===transactionKey) {
        autoMapStatus('сражение → жду подтверждение удара',{
          revision:HK_BATTLE_SINGLE_TAP_REV
        });
        recordDiagnostic('battle-attack-repeat-prevented',{
          revision:HK_BATTLE_SINGLE_TAP_REV,
          expectedCost:hasExpected?numericExpected:null,
          pendingMs:Date.now()-battleAttackPending.sentAt
        });
        return {handled:true,success:false,reason:'awaiting-server-receipt'};
      }
      let action=null,elapsed=Date.now();""",
    'guard existing unresolved dispatch')

rep("""      if (!dispatchBattleOverlaySafeTap(action,'battle-open-modal-confirm')) {
        return {handled:true,success:false,reason:'tap-failed'};
      }

      const started=Date.now();""",
"""      if (!dispatchBattleOverlaySafeTap(action,'battle-open-modal-confirm')) {
        return {handled:true,success:false,reason:'tap-failed'};
      }
      battleAttackPending.key=transactionKey;
      battleAttackPending.sentAt=Date.now();
      recordDiagnostic('battle-attack-dispatched-once',{
        revision:HK_BATTLE_SINGLE_TAP_REV,
        expectedCost:hasExpected?numericExpected:null,
        resolvedCost
      });

      const started=Date.now();""",
    'record dispatched attack before receipt wait')

rep("""        if (swordSpent || enemyStateChanged || (rewardArrived && !battleEnemyModalRoot())) {
          recordDiagnostic('battle-attack-receipt-verified',{""",
"""        if (swordSpent || enemyStateChanged || (rewardArrived && !battleEnemyModalRoot())) {
          battleAttackPending.key='';
          battleAttackPending.sentAt=0;
          recordDiagnostic('battle-attack-receipt-verified',{""",
    'clear ledger only on verified mutation')

rep("""      recordDiagnostic('battle-attack-receipt-pending',{
        revision:HK_BATTLE_ATTACK_RECEIPT_REV,
        expectedCost:hasExpected?numericExpected:null,
        resolvedCost,reason:'no-server-state-change'
      });""",
"""      autoMapStatus('сражение → жду подтверждение удара',{
        revision:HK_BATTLE_SINGLE_TAP_REV
      });
      recordDiagnostic('battle-attack-receipt-pending',{
        revision:HK_BATTLE_ATTACK_RECEIPT_REV,
        expectedCost:hasExpected?numericExpected:null,
        resolvedCost,reason:'no-server-state-change',
        resendBlocked:!!battleAttackPending.key
      });""",
    'unknown purchase stops repeat clicks')

# While the receipt is unknown no modal closure/reopening may cause a second
# purchase; a manual action that changes swords/board releases the ledger.
rep("""    async function battleRecoverStalledEnemyModal(source='attack-not-accepted') {
      const root=battleEnemyModalRoot();
      if (!root || !battleAutoEnabled()) return false;""",
"""    async function battleRecoverStalledEnemyModal(source='attack-not-accepted') {
      const root=battleEnemyModalRoot();
      if (!root || !battleAutoEnabled()) return false;
      if (battleAttackPending.key) {
        autoMapStatus('сражение → жду подтверждение удара',{
          revision:HK_BATTLE_SINGLE_TAP_REV,source
        });
        return false;
      }""",
    'no close during pending purchase')

rep("""        if (!result.success) {
          await battleRecoverStalledEnemyModal(result.reason);
          recordDiagnostic('battle-open-modal-priority-stop',{""",
"""        if (!result.success) {
          if (result.reason!=='awaiting-server-receipt' &&
              result.reason!=='no-server-state-change') {
            await battleRecoverStalledEnemyModal(result.reason);
          }
          recordDiagnostic('battle-open-modal-priority-stop',{""",
    'do not recovery-dismiss pending purchase')

# Keep previous exit guard unchanged; export traceable revisions for diagnostics.
marker="      battleAttackReceiptRevision:HK_BATTLE_ATTACK_RECEIPT_REV,"
rep(marker,marker+"\n      battleMobilePriceRevision:HK_BATTLE_MOBILE_PRICE_REV,\n      battleSingleTapRevision:HK_BATTLE_SINGLE_TAP_REV,",'debug revision export')
p.write_text(s,encoding='utf-8')
print('PATCH_BATTLE_MOBILE_PRICE_1_18_100=PASS')
