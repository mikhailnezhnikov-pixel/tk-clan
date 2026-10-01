const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');

const s=fs.readFileSync(process.argv[2]||'/tmp/HamsterKingMobile.user.js','utf8');
function section(a,b){
  const i=s.indexOf(a),j=s.indexOf(b,i+a.length);
  assert(i>=0&&j>i,'section absent: '+a);
  return s.slice(i,j);
}
const actionCode=section('    function battleEnemyModalActionButton(expectedCost=null) {',
                         '    function battleEnemyModalRoot() {');
const heading='Красный вояка МОЖНО ОТЫСКАТЬ';
const bounds={left:38,top:185,width:324,height:335};
const buttonBounds={left:114,top:446,width:168,height:49};
const rewardBounds={left:70,top:315,width:42,height:50};
function node(tag,text,rect,children=[]){
  return {
    tagName:tag,
    isConnected:true,
    disabled:false,
    innerText:text,
    textContent:text,
    style:{pointerEvents:'auto'},
    getAttribute:()=>null,
    getBoundingClientRect:()=>rect,
    querySelectorAll:()=>children,
    matches:q=>q.includes(tag.toLowerCase())&&tag!=='span',
    onclick:tag==='button'?()=>{}:null,
  };
}
function actionCase(price,{spinner=false,overlap=false}={}){
  const reward1=node('span','x1',rewardBounds);
  const reward6=node('span','x6',{left:300,top:315,width:40,height:50});
  const button=node('button',spinner?'':('⚔ '+price),buttonBounds);
  const priceInner=node('span',String(price),{left:190,top:454,width:16,height:32});
  const spin=node('span','',{left:190,top:454,width:16,height:16});
  const root=node('div',heading,bounds,[reward1,reward6,button,spinner?spin:priceInner]);
  const diagnostics=[];
  const env={
    document:{querySelectorAll:()=>[root]},
    window:{innerWidth:400,innerHeight:820},
    visible:()=>true,
    clean:v=>String(v??''),
    getComputedStyle:e=>({cursor:e.tagName==='button'?'pointer':'default'}),
    recordDiagnostic:(t,d)=>diagnostics.push([t,d]),
    HK_BATTLE_MODAL_ACTION_RECOVERY_REV:'legacy',
    HK_BATTLE_OPEN_MODAL_PRIORITY_REV:'legacy',
  };
  vm.createContext(env);
  vm.runInContext(actionCode,env);
  const chosen=env.battleEnemyModalActionButton(null);
  const inferred=env.battleEnemyModalActionCost(chosen);
  const expected=env.battleEnemyModalActionButton(price);
  return {chosen,inferred,expected,button,diagnostics};
}

for(const cost of [1,2]){
  const result=actionCase(cost);
  assert.equal(result.chosen,result.button,'unknown-cost mobile modal must choose full button cost '+cost);
  assert.equal(result.inferred,cost,'mobile price must infer '+cost+' swords');
  assert.equal(result.expected,result.button,'known-cost mobile modal must choose '+cost+' swords');
}
assert.equal(actionCase(2,{spinner:true}).chosen,null,'blank loading action must not be tapped');

// Real mobile buy buttons often wrap a narrow price span. The ancestor must
// win over the digit-only child; synthetic click targeting the span is brittle.
if (s.includes('battle-enemy-action-parent-20261001-r1')) {
  for(const cost of [1,2,4]) {
    const digit=node('span',String(cost),{left:193,top:455,width:16,height:28});
    const purchase=node('button','⚔ '+cost,buttonBounds,[digit]);
    const reward=node('span','x1',rewardBounds);
    const popup=node('div',heading,bounds,[reward,purchase,digit]);
    digit.parentElement=purchase;
    purchase.parentElement=popup;
    reward.parentElement=popup;
    popup.contains=child=>child===purchase||child===digit||child===reward;
    const env={
      document:{querySelectorAll:()=>[popup]},
      window:{innerWidth:400,innerHeight:820},
      visible:()=>true,
      clean:v=>String(v??''),
      getComputedStyle:e=>({cursor:e.tagName==='button'?'pointer':'default'}),
      recordDiagnostic:()=>{},
      HK_BATTLE_MODAL_ACTION_RECOVERY_REV:'legacy',
      HK_BATTLE_OPEN_MODAL_PRIORITY_REV:'legacy'
    };
    vm.createContext(env);
    vm.runInContext(actionCode,env);
    assert.equal(env.battleEnemyModalActionButton(null),purchase,
      'numeric inner span must be promoted to full buy button for '+cost+' swords');
    assert.equal(env.battleEnemyModalActionCost(purchase),cost);
  }
}


// The HUD overlays are temporarily relocated above the modal; after it
// closes their normal bottom positions must be restored.
const battleCode=section('    function updateBattleAutoToggle(isBattle = null) {',
                         '    function ensureBattleAutoToggle(isBattle) {');
const autoCode=section('    function updateAutoMapToggle(showOverride=null) {',
                       '    function ensureAutoMapToggle() {');
let modalOpen=true;
const battleHud={style:{},textContent:'',id:'hkBattleAutoToggle'};
const mapHud={style:{},textContent:'',id:'hkTreasureAutoMapToggle'};
const hudEnv={
  battleAutoToggle:battleHud,
  autoMapToggle:mapHud,
  battleAutoEnabled:()=>true,
  autoMapEnabled:()=>true,
  autoMapLastStatus:'сражение',
  battleEnemyModalRoot:()=>modalOpen?{}:null,
  autoMapTreasuryIntroModalRoot:()=>null,
  treasureEventContextVisible:()=>true,
  either:(ru)=>ru
};
vm.createContext(hudEnv);
vm.runInContext(battleCode+autoCode,hudEnv);
hudEnv.updateBattleAutoToggle(true);
hudEnv.updateAutoMapToggle(true);
if(s.includes('battle-bottom-hud-status-20261001-r1')){
  const bottom='calc(env(safe-area-inset-bottom, 0px) + 8px)';
  assert.equal(battleHud.style.top,'auto');
  assert.equal(battleHud.style.bottom,bottom);
  assert.equal(battleHud.style.right,'8px');
  assert.equal(mapHud.style.top,'auto');
  assert.equal(mapHud.style.bottom,bottom);
  assert.equal(mapHud.style.left,'8px');
  assert.equal(mapHud.style.right,'auto');
  assert(mapHud.textContent.includes('\nсражение'),'diagnostic status must remain visible');
  modalOpen=false;
  hudEnv.updateBattleAutoToggle(true);
  hudEnv.updateAutoMapToggle(true);
  assert.equal(battleHud.style.bottom,bottom,'right battle HUD must stay at bottom');
  assert.equal(mapHud.style.bottom,bottom,'left map HUD must stay at bottom');
}else{
  assert.equal(battleHud.style.top,'132px');
  assert.equal(battleHud.style.bottom,'auto');
  assert.equal(mapHud.style.top,'85px');
  assert.equal(mapHud.style.bottom,'auto');
  modalOpen=false;
  hudEnv.updateBattleAutoToggle(true);
  hudEnv.updateAutoMapToggle(true);
  assert.equal(battleHud.style.top,'auto');
  assert.equal(battleHud.style.bottom,'154px');
  assert.equal(mapHud.style.top,'auto');
  assert.equal(mapHud.style.bottom,'202px');
}

console.log('BATTLE_MOBILE_PRICE_RUNTIME=PASS (1/2/4 swords, nested action parent, spinner, bottom corner HUD and status)');
