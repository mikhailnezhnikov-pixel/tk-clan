(function(w){
  'use strict';
  const C=w.TopKingBattleCore||{},state={scene:null,adapter:null,queue:null,ready:false,pending:null,hpCallback:null};
  const kind=war=>/bot|бот|boss|босс/i.test(String(war?.opponent||''))?'bot':'clan';
  function activeHp(war){const eh=Number(war?.opponent_hp),em=Number(war?.opponent_hp_max),oh=Number(war?.our_hp),om=Number(war?.our_hp_max);return Number.isFinite(em)&&em>0?{hp:eh,max:em,side:'enemy'}:{hp:oh,max:om,side:'ours'}}
  function emitHp(hp,max,meta){if(state.hpCallback&&Number.isFinite(Number(hp))&&Number.isFinite(Number(max)))state.hpCallback(Number(hp),Number(max),meta||{})}
  async function init(){
    if(state.ready)return true;if(!w.PIXI||!w.gsap||!C.BattleScene||!C.WarEventAdapter||!C.BattleEventQueue)return false;
    const canvas=document.getElementById('battle-canvas'),host=document.getElementById('battle-stage');if(!canvas||!host)return false;
    state.adapter=new C.WarEventAdapter();state.scene=new C.BattleScene({PIXI:w.PIXI,gsap:w.gsap,canvas,host});await state.scene.init(event=>emitHp(event.remainingHp,event.maxHp,{animated:true,event}));state.queue=new C.BattleEventQueue(event=>state.scene.play(event));state.ready=true;
    if(state.pending){const p=state.pending;state.pending=null;update(p.war,p.info,p.options)}return true;
  }
  function update(war,info,options={}){
    if(typeof options.onHp==='function')state.hpCallback=options.onHp;
    if(!state.ready){state.pending={war,info,options};init().catch(err=>console.error('[TopKingBattleV4:init]',err));return true}
    if(!war){state.queue.clear();state.adapter.reset();state.scene.sync(null,info);return true}
    state.scene.sync(war,info);document.getElementById('battle-stage')?.setAttribute('data-opponent-kind',kind(war));
    const result=state.adapter.ingest(war),hp=activeHp(war);
    if(result.initial||result.forceSync)emitHp(hp.hp,hp.max,{animated:false,initial:result.initial});
    if(result.events.length)state.queue.enqueueMany(result.events);return true;
  }
  function destroy(){state.queue?.clear();state.scene?.destroy();state.adapter?.reset();state.scene=null;state.ready=false}
  w.TopKingBattleV4={version:'4.0.0-milestone-1',init,update,destroy};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>init().catch(console.error),{once:true});else init().catch(console.error);
})(window);
