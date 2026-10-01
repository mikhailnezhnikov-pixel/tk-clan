const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const s=fs.readFileSync(process.argv[2]||'/tmp/HamsterKingMobile.user.js','utf8');
function section(a,b){
  const i=s.indexOf(a),j=s.indexOf(b,i+a.length);
  assert(i>=0&&j>i,'missing section '+a);
  return s.slice(i,j);
}
const gate=section('    function battleExitState() {','    function battleLeaveBackButton(');
function gateCase({board=[{hp:1,slot:7}],swords=13,modal=false,claimed=true,recovered=true,signature='BATTLE_COMPLETE',room=true,reward=false}={}){
  const diagnostics=[];
  const env={
    getSignature:()=>signature,getBattleBoard:()=>board,
    getBattleAttack:()=>swords,battleEggOfferTarget:()=>null,
    battleEnemyModalRoot:()=>modal?{}:null,
    battleVictoryElement:()=>reward?{}:null,
    battleVictoryModalRoot:()=>null,
    battleRewardConfirmOnlyPending:()=>false,
    battleRecoverFinalRewardClaimed:()=>recovered,
    battleScreenVisiblyCurrent:()=>room,
    HK_BATTLE_NO_PREMATURE_EXIT_REV:'battle-no-premature-exit-20261001-r1',
    recordDiagnostic:(name,data)=>diagnostics.push({name,data}),
  };
  vm.createContext(env);
  vm.runInContext("let battleFinalRewardClaimed="+String(claimed)+",battleFinalRewardClaimedAt=100;"+gate,env);
  return {...vm.runInContext("({gate:battleExitState(),claimed:battleFinalRewardClaimed})",env),diagnostics};
}
let r=gateCase();
assert.equal(r.gate.allowed,false,'1 HP enemy with 13 swords forbids exit even after stale reward claim');
assert.equal(r.gate.reason,'attack-available');
assert.equal(r.claimed,false,'stale reward claim must be invalidated');
assert.equal(gateCase({modal:true}).gate.reason,'enemy-modal-pending','an open enemy modal forbids paid exit');
assert.equal(gateCase({board:[],claimed:true}).gate.allowed,true,'fully cleared activated room may leave');
assert.equal(gateCase({board:[{hp:30,slot:7}],swords:13,claimed:false,recovered:false}).gate.reason,
  'no-attack-available','insufficient swords allows exit');
assert.equal(gateCase({swords:null,claimed:false,recovered:false}).gate.allowed,false,
  'unknown balance cannot justify exit');
assert.equal(gateCase({board:[],claimed:false,recovered:false,reward:true}).gate.reason,
  'final-reward-pending','unclaimed reward forbids exit');

const boardCode=section('    function getBattleBoard() {','    function battleEggOfferCost(');
const fairEnv={
  BATTLE_SIZE:12,BATTLE_FIRST_SLOT:1,
  battleFairSlots:()=>[{shop_lot_id:'mf_treasurelot_enemy_type_01_1_sl1',is_bought:true}],
  recordDiagnostic:()=>{},
  document:{querySelectorAll:()=>{throw Error('DOM fallback is forbidden when fair reports purchased slots');}},
};
vm.createContext(fairEnv);
vm.runInContext(boardCode,fairEnv);
assert.equal(vm.runInContext('getBattleBoard().filter(Boolean).length',fairEnv),0,
  'purchased fair slots must beat stale DOM enemies');

const confirm=section('    async function battleConfirmAlreadyOpenEnemyModal(',
  '    const battleOpenModalStall=');
function confirmCase({redraw=false,spend=false,spinner=false}={}){
  let clock=0,clicks=0;
  const first={isConnected:true},second={isConnected:true},action={
    isConnected:true,disabled:false,getAttribute:()=>null
  };
  const initial=[{hp:1,slot:7,lotId:'enemy_type_01_1_sl7'}];
  const state={root:first,swords:13,board:initial};
  const env={
    Date:{now:()=>{clock+=200;return clock;}},
    battleEnemyModalRoot:()=>state.root,
    battleAutoRunId:1,battleAutoEnabled:()=>true,
    battleEnemyModalActionButton:()=>spinner?null:action,
    battleEnemyModalActionCost:()=>1,
    getBattleAttack:()=>state.swords,
    getBattleBoard:()=>state.board,
    getSignature:()=> 'BATTLE|SWORDS='+state.swords,
    battleScrollTargetIntoViewportAsync:async()=>true,
    dispatchBattleOverlaySafeTap:()=>{
      clicks++;
      if (redraw) state.root=second;
      if (spend) state.swords=12;
      return true;
    },
    getComputedStyle:()=>({pointerEvents:'auto'}),
    battleVictoryElement:()=>null,
    battleVictoryModalRoot:()=>null,
    setTimeout:callback=>callback(),
    recordDiagnostic:()=>{},
    HK_BATTLE_ATTACK_RECEIPT_REV:'battle-attack-state-receipt-20261001-r1',
  };
  vm.createContext(env);
  vm.runInContext(confirm,env);
  return env.battleConfirmAlreadyOpenEnemyModal(1,1).then(result=>({result,clicks}));
}
(async()=>{
  const redraw=await confirmCase({redraw:true});
  assert.equal(redraw.result.success,false,'modal re-render alone does not prove an attack');
  assert.equal(redraw.clicks,1,'do not double-tap a pending attack');
  const paid=await confirmCase({spend:true});
  assert.equal(paid.result.success,true,'actual sword debit proves accepted attack');
  assert.equal(paid.clicks,1,'single attack must tap once');
  const loading=await confirmCase({spinner:true});
  assert.equal(loading.result.success,false,'price spinner without button cannot be clicked');
  assert.equal(loading.clicks,0,'no blind coordinate taps while price loads');
  console.log('BATTLE_STATE_RECEIPT_RUNTIME=PASS (10 scenarios: attackable, modal, clear, insufficient, unknown, reward, fair, redraw, debit, spinner)');
})().catch(error=>{console.error(error);process.exitCode=1;});
