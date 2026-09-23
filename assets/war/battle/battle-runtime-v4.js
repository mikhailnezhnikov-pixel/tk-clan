(function(w){
  'use strict';
  if(w.TopKingBattleV4)return;
  const C=w.TopKingBattleCore||{},state={scene:null,adapter:null,queue:null,ready:false,initializing:null,pending:null,hpCallback:null,eventCallback:null,generation:0};
  function activeHp(war){const eh=Number(war?.opponent_hp),em=Number(war?.opponent_hp_max),oh=Number(war?.our_hp),om=Number(war?.our_hp_max);return Number.isFinite(em)&&em>0?{hp:eh,max:em,side:'enemy'}:{hp:oh,max:om,side:'ours'}}
  function emitHp(hp,max,meta){if(state.hpCallback&&Number.isFinite(hp)&&Number.isFinite(max))state.hpCallback(hp,max,meta||{})}
  async function init(){
    if(state.ready)return true;
    if(state.initializing)return state.initializing;
    const generation=state.generation;
    const promise=(async()=>{
      if(!w.PIXI||!w.gsap||!C.BattleScene)return false;
      const canvas=document.getElementById('battle-canvas'),host=document.getElementById('battle-stage');if(!canvas||!host)return false;
      const scene=new C.BattleScene({PIXI:w.PIXI,gsap:w.gsap,canvas,host});state.scene=scene;
      try{
        await scene.init(event=>{if(generation!==state.generation)return;state.eventCallback?.(event);const shown=activeHp(event.snapshot||{});if(shown.side===event.defender)emitHp(event.remainingHp,event.maxHp,{animated:true,event})});
        if(generation!==state.generation)return false;
        state.adapter=new C.WarEventAdapter();state.queue=new C.BattleEventQueue(event=>scene.play(event));state.ready=true;
        host.classList.remove('battle-v2-failed');
        if(state.pending){const p=state.pending;state.pending=null;update(p.war,p.info,p.options)}
        return true;
      }catch(err){scene.destroy();if(generation===state.generation){host.classList.add('battle-v2-failed');state.scene=null}throw err}
    })();state.initializing=promise;
    try{return await promise}finally{if(state.initializing===promise)state.initializing=null}
  }
  function update(war,info,options={}){
    if(typeof options.onHp==='function')state.hpCallback=options.onHp;
    state.eventCallback=typeof options.onEvent==='function'?options.onEvent:null;
    if(!state.ready){state.pending={war:war?{...war}:null,info,options};init().catch(err=>console.error('[TopKingBattleV4:init]',err));return true}
    if(!war){state.queue.clear();state.scene.reset();state.adapter.reset();state.scene.sync(null);emitHp(0,0,{animated:false});return true}
    const result=state.adapter.ingest(war),hp=activeHp(war);
    if(result.initial){state.queue.clear();state.scene.reset()}
    state.scene.sync(war,info);
    // An unchanged poll must not leap ahead of a queued contact.
    if(result.initial||(result.forceSync&&!state.queue.running&&!state.queue.items.length))emitHp(hp.hp,hp.max,{animated:false,initial:result.initial});
    if(result.events.length)state.queue.enqueueMany(result.events);return true;
  }
  function destroy(){state.generation++;state.queue?.clear();state.scene?.destroy();state.adapter?.reset();Object.assign(state,{scene:null,adapter:null,queue:null,pending:null,hpCallback:null,eventCallback:null,ready:false,initializing:null})}
  w.TopKingBattleV4={version:'4.1.0-character-motion',init,update,destroy};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>init().catch(console.error),{once:true});else init().catch(console.error);
})(window);
