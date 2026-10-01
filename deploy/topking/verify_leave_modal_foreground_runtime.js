const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');

const file=process.argv[2]||'/tmp/HamsterKingMobile.user.js';
const text=fs.readFileSync(file,'utf8');
const start=text.indexOf('    function autoMapReturnMapConfirmed() {');
const end=text.indexOf('    function autoMapPromoteActionTarget(element,root=null) {',start);
assert(start>=0 && end>start,'leave modal code not found');
const code=text.slice(start,end);

function element(value,rect,children=[],explicit=false) {
  const node={
    innerText:value,
    textContent:value,
    disabled:false,
    matches:()=>explicit,
    isConnected:true,
    getBoundingClientRect:()=>rect,
    querySelectorAll:()=>children,
    contains(child){return children.includes(child);},
  };
  return node;
}
const rect={left:45,top:170,width:310,height:405};
const mainPriceRect={left:109,top:485,width:185,height:53};

function test(root,map={title:false,room:false,cards:false,journey:false}) {
  const children=root?.querySelectorAll()||[];
  const context={
    window:{innerWidth:400,innerHeight:800},
    document:{querySelectorAll:()=>root?[root]:[]},
    visible:()=>true,
    clean:value=>String(value??''),
    battleElementFromPointIgnoringOverlays:()=>children[0]||root,
    treasureGuideScreenVisible:()=>map.title,
    autoMapTreasuryForeground:()=>false,
    battleScreenVisiblyCurrent:()=>map.room,
    autoMapMiniGameForeground:()=>map.room,
    autoMapMapIsForeground:()=>map.cards,
    autoMapJourneyButton:()=>map.journey?{}:null,
    autoMapElementIsForeground:()=>map.journey,
  };
  return vm.runInNewContext(code+'; ({modal:autoMapLeaveModalRoot(),map:autoMapReturnMapConfirmed()})',context);
}

const page=element('Сражение · 101K · Покинуть локацию',rect,[
  element('101K',{left:180,top:200,width:60,height:40}),
  element('Покинуть локацию',{left:80,top:520,width:240,height:48})
]);
assert.equal(test(page).modal,null,'the room and 101K wallet must not look like a leave modal');

const pageWithUnrelatedTen=element('Сражение · Покинуть локацию · 10',rect,[
  element('10',mainPriceRect),
  element('Покинуть локацию',{left:80,top:520,width:240,height:48})
]);
assert.equal(test(pageWithUnrelatedTen).modal,null,'ordinary room without a dialog/prompt/back must not count');

const price=element('10',mainPriceRect);
const back=element('Назад',{left:70,top:480,width:95,height:50});
const real=element('Покинуть локацию · Продолжить? · Назад · 10',rect,[price,back],true);
assert.equal(test(real).modal,real,'real foreground leave dialog with a 10 action must be found');

assert.equal(test(real,{title:true,room:true,cards:true}).map,false,'background map cannot prove exit while battle remains foreground');
assert.equal(test(null,{title:true,room:false,cards:true}).map,true,'foreground map proves exit');
assert.equal(test(null,{title:true,room:false,cards:false,journey:true}).map,true,'foreground new journey proves exit');
assert.equal(test(null,{title:true,room:false,cards:false,journey:false}).map,false,'title alone cannot prove exit');

console.log('LEAVE_MODAL_FOREGROUND_RUNTIME=PASS (6 scenarios)');
