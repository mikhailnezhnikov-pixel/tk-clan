from pathlib import Path
import sys

s=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/HamsterKingMobile.user.js').read_text(encoding='utf-8')

def section(a,b):
    i=s.find(a)
    if i<0: raise SystemExit('missing section: '+a)
    j=s.find(b,i+len(a))
    if j<0: raise SystemExit('missing section end: '+b)
    return s[i:j]

required=[
    '// @version      '+('1.18.101' if 'battle-bottom-hud-status-20261001-r1' in s else '1.18.100'),
    "const BUILD_VERSION = '"+('1.18.101' if 'battle-bottom-hud-status-20261001-r1' in s else '1.18.100')+"';",
    'battle-mobile-price-action-20261001-r1',
    'battle-single-tap-until-receipt-20261001-r1',
    'battle-no-premature-exit-20261001-r1',
    'battle-attack-state-receipt-20261001-r1',
    'treasury-intro-mobile-ack-20261001-r1',
    'leave-modal-foreground-truth-20261001-r1'
]
for marker in required:
    if marker not in s:raise SystemExit('missing release marker: '+marker)

action=section('function battleEnemyModalActionButton(expectedCost=null) {','function battleEnemyModalRoot() {')
correct_numeric=r'const numericMatch=text.match(/(?:^|\s)(\d{1,4})(?:\s|$)/);'
correct_values=r'const values=[...text.matchAll(/(?:^|\s)(\d{1,4})(?=\s|$)/g)]'
bad_numeric=r'const numericMatch=text.match(/(?:^|\\s)(\\d{1,4})(?:\\s|$)/);'
bad_values=r'const values=[...text.matchAll(/(?:^|\\s)(\\d{1,4})(?=\\s|$)/g)]'
if correct_numeric not in action or correct_values not in action:
    raise SystemExit('literal JS regex does not parse 1/2 sword labels')
if bad_numeric in action or bad_values in action:
    raise SystemExit('double-escaped literal JS price regex regressed')
if "new RegExp('(?:^|\\\\s)'+costText+'(?:\\\\s|$)')" not in action:
    raise SystemExit('string-based RegExp escaped incorrectly')

confirm=section('const battleAttackPending=','const battleOpenModalStall=')
for marker in [
    "const transactionKey=String(beforeSwords)+'|'+beforeBoard;",
    "if (battleAttackPending.key===transactionKey)",
    "reason:'awaiting-server-receipt'",
    "battleAttackPending.key=transactionKey;",
    "battleAttackPending.sentAt=Date.now();",
    "battleAttackPending.key='';",
    "swordSpent || enemyStateChanged || (rewardArrived && !battleEnemyModalRoot())",
    "resendBlocked:!!battleAttackPending.key"
]:
    if marker not in confirm:raise SystemExit('single-tap receipt contract missing: '+marker)
if not (confirm.index('battleAttackPending.key=transactionKey;') <
        confirm.index("if (swordSpent || enemyStateChanged ||")):
    raise SystemExit('pending ledger created after receipt, unsafe')

stall=section('async function battleRecoverStalledEnemyModal(','async function runBattleOpenEnemyModalRecovery(')
if "if (battleAttackPending.key)" not in stall:
    raise SystemExit('stalled recovery may close unresolved purchase')
run=section('async function runBattleOpenEnemyModalRecovery(','function battleActionButton(')
if "result.reason!=='no-server-state-change'" not in run:
    raise SystemExit('unconfirmed purchase can be retried after timeout')

battleHud=section('function updateBattleAutoToggle(isBattle = null) {','function ensureBattleAutoToggle(')
mapHud=section('function updateAutoMapToggle(showOverride=null) {','function ensureAutoMapToggle()')
for marker in ["const battleHudTop=enemyModalOpen?'132px':'auto';",
               "const battleHudBottom=enemyModalOpen?'auto':'154px';"]:
    if marker not in battleHud:raise SystemExit('battle HUD blocks mobile action: '+marker)
for marker in ["const hudBottom=(treasuryIntro||enemyModalOpen)?'auto':'202px';",
               "const hudTop=(treasuryIntro||enemyModalOpen)?'85px':'auto';"]:
    if marker not in mapHud:raise SystemExit('map HUD blocks mobile action: '+marker)

exitGate=section('function battleExitState() {','function battleLeaveBackButton(')
for marker in [
    "reason:'enemy-modal-pending'",
    "reason:'attack-available'",
    "reason:'no-attack-available'"
]:
    if marker not in exitGate:raise SystemExit('1.18.99 exit protection lost: '+marker)

print('BATTLE_MOBILE_PRICE_CONTRACT=PASS')
