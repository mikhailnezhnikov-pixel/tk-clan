const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');

const src=fs.readFileSync(process.argv[2]||'/tmp/HamsterKingMobile.user.js','utf8');
function part(start,end) {
  const a=src.indexOf(start);
  const b=src.indexOf(end,a+start.length);
  assert(a>=0 && b>a,'missing test section '+start);
  return src.slice(a,b);
}

const titleRect={left:126,top:364,width:148,height:32};
const rootRect={left:30,top:270,width:340,height:300};
const actionRect={left:92,top:482,width:216,height:53};
const closeRect={left:330,top:292,width:23,height:24};
const state={open:true,withButton:true,disabled:false,battle:false,clicked:0};
function node(text,rect,opts={}) {
  return {
    innerText:text,textContent:text,isConnected:true,disabled:false,
    getAttribute:()=>null,getBoundingClientRect:()=>rect,
    matches:selector=>opts.button?selector.includes('button'):false,
    querySelectorAll:()=>opts.children||[],
    contains:other=>(opts.children||[]).includes(other),
    click:()=>{}
  };
}
const title=node('Сокровищница',titleRect);
const close=node('×',closeRect,{button:true});
const button=node('',actionRect,{button:true});
button.click=()=>{state.clicked++;state.open=false;};
const root=node('Сокровищница',rootRect,{children:[title,close,button]});
root.isConnected=true;
const doc={
  querySelectorAll:selector=>{
    if (selector.startsWith('h1,h2,h3')) return [title];
    if (selector.includes('[role="dialog"]')) return state.open?[root]:[];
    return [];
  }
};
const statuses=[];
const core=part('    function autoMapTreasuryForeground() {','    function autoMapTreasuryCorridorModalRoot() {');
const env={
  window:{innerWidth:400,innerHeight:800},
  document:doc,
  visible:e=>e && e.isConnected!==false,
  clean:v=>String(v??''),
  battleScreenVisiblyCurrent:()=>state.battle,
  autoMapElementIsForeground:()=>true,
  battleElementFromPointIgnoringOverlays:(x,y)=>y>460?button:title,
  getComputedStyle:e=>({pointerEvents:state.disabled && e===button?'none':'auto',cursor:e===button?'pointer':'default'}),
  autoMapToggle:null,
  autoMapEnabled:()=>true,
  autoMapWaitActionGap:async()=>{},
  autoMapStatus:label=>statuses.push(label),
  recordDiagnostic:()=>{},
  deviceNeutralActivate:async(e,label,accepted)=>{e.click();return accepted();},
  battlePointBelongsToElement:()=>true,
  dispatchMinigameOverlaySafeTapAt:()=>false,
  waitDeviceNeutralCondition:async()=>false,
  setTimeout:()=>1,
  runAutoMapTick:async()=>true,
  Date,
};
vm.createContext(env);
vm.runInContext('const HK_TREASURY_INTRO_REV="treasury-intro-mobile-ack-20261001-r1"; let autoMapLastActionAt=0,lastSignature="",autoMapRetryNotBefore=0;\n'+core,env);
assert.equal(env.autoMapTreasuryForeground(),true,'Treasury heading must be recognized');
assert.equal(env.autoMapTreasuryIntroModalRoot(),root,'foreground intro must be recognized');
assert.equal(env.autoMapTreasuryIntroAction(root),button,'blank lower button must be targeted');
state.disabled=true;
assert.equal(env.autoMapTreasuryIntroAction(root),null,'disabled/pointer-blocked action must never be clicked');
state.disabled=false;
state.battle=true;
assert.equal(env.autoMapTreasuryIntroModalRoot(),null,'active battle blocks false Treasury intro');
state.battle=false;

(async()=>{
  const acknowledged=await env.autoMapAcknowledgeTreasuryIntro('mobile-fixture');
  assert.equal(acknowledged,true,'blank mobile action must be acknowledged');
  assert.equal(state.clicked,1,'intro must be clicked exactly once');
  assert.equal(env.autoMapTreasuryIntroModalRoot(),null,'intro must be gone after acknowledgement');
  assert(statuses.includes('сокровищница → подтверждаю вход'));
  // Starting an already-running battle exit while Treasury is foreground must
  // yield immediately, without clicking Leave, confirming 10, or trying 3x.
  const exit=part('    async function autoMapRecoverCompletedBattleExit','    function autoMapModalPrimaryButton');
  let exitTaps=0,handoffs=0;
  const other={
    ...env,
    autoMapTreasuryForeground:()=>true,
    autoMapReturnMapConfirmed:()=>false,
    battleRecoverFinalRewardClaimed:()=>true,
    autoMapExitButton:()=>{exitTaps++;return null;},
    autoMapStatus:label=>{if(label==='сокровищница → вход') handoffs++;},
    recordDiagnostic:()=>{},
  };
  vm.createContext(other);
  vm.runInContext('const HK_TREASURY_BATTLE_HANDOFF_REV="treasury-battle-foreground-handoff-20261001-r1";let battleFinalRewardClaimed=true,battleFinalRewardClaimedAt=100,autoMapRetryNotBefore=900,lastSignature="BATTLE";\n'+exit,other);
  const handedOff=await other.autoMapRecoverCompletedBattleExit('fixture');
  assert.equal(handedOff,true,'battle exit coroutine must release to Treasury');
  assert.equal(exitTaps,0,'battle exit cannot keep clicking after Treasury appears');
  assert.equal(handoffs,1);
  const released=vm.runInContext('({claimed:battleFinalRewardClaimed,at:battleFinalRewardClaimedAt,retry:autoMapRetryNotBefore})',other);
  assert.equal(released.claimed,false);
  assert.equal(released.at,0);
  assert.equal(released.retry,0);

  console.log('TREASURY_INTRO_RUNTIME=PASS (7 scenarios; blank button, disabled button, true foreground, battle guard, one click, real acknowledgment, battle handoff)');
})().catch(error=>{console.error(error);process.exitCode=1;});
