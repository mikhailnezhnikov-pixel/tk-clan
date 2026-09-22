(function(w){
  'use strict';
  const C=w.TopKingBattleCore||{},state={scene:null,adapter:null,queue:null,ready:false,initializing:null,pending:null,hpCallback:null};
  const kind=war=>{
    const explicit=String(war?.opponent_type||war?.enemy_type||war?.kind||'').trim().toLowerCase();
    if(explicit.includes('bot')||explicit.includes('boss')||explicit.includes('npc'))return 'bot';
    return /(\bбот\b|\bbot\b|\bboss\b|\bnpc\b|рейд|raid|страж|guardian|robot|drone)/i.test(String(war?.opponent||''))?'bot':'clan';
  };
  function activeHp(war){const eh=Number(war?.opponent_hp),em=Number(war?.opponent_hp_max),oh=Number(war?.our_hp),om=Number(war?.our_hp_max);return Number.isFinite(em)&&em>0?{hp:eh,max:em,side:'enemy'}:{hp:oh,max:om,side:'ours'}}
  function emitHp(hp,max,meta){if(state.hpCallback&&Number.isFinite(Number(hp))&&Number.isFinite(Number(max)))state.hpCallback(Number(hp),Number(max),meta||{})}
  async function init(){
    if(state.ready)return true;
    if(state.initializing)return state.initializing;
    state.initializing=(async()=>{
      if(!w.PIXI||!w.gsap||!C.BattleScene||!C.WarEventAdapter||!C.BattleEventQueue)return false;
      const canvas=document.getElementById('battle-canvas'),host=document.getElementById('battle-stage');if(!canvas||!host)return false;
      state.adapter=new C.WarEventAdapter();
      state.scene=new C.BattleScene({PIXI:w.PIXI,gsap:w.gsap,canvas,host});
      try{
        await state.scene.init(event=>{const shown=activeHp(event.snapshot||{});if(shown.side===event.defender)emitHp(event.remainingHp,event.maxHp,{animated:true,event})});
      }catch(err){
        host.classList.add('battle-v2-failed');
        try{state.scene?.destroy()}catch(_){}
        state.scene=null;state.adapter=null;
        throw err;
      }
      state.queue=new C.BattleEventQueue(event=>state.scene.play(event));
      state.ready=true;
      if(state.pending){const p=state.pending;state.pending=null;update(p.war,p.info,p.options)}
      return true;
    })();
    try{return await state.initializing}finally{state.initializing=null}
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
  function destroy(){state.queue?.clear();state.scene?.destroy();state.adapter?.reset();state.scene=null;state.adapter=null;state.queue=null;state.pending=null;state.hpCallback=null;state.ready=false}
  w.TopKingBattleV4={version:'4.0.7-single-init',init,update,destroy};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>init().catch(console.error),{once:true});else init().catch(console.error);
})(window);
