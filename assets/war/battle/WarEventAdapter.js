(function(w){
  'use strict';
  const num=v=>{if(v==null||v==='')return null;const n=Number(v);return Number.isFinite(n)?n:null};
  class WarEventAdapter{
    constructor(){this.prev=null;this.key=''}
    reset(){this.prev=null;this.key=''}
    identity(war){return [war?.opponent||'',war?.started_at||war?.start_at||'',war?.war_id||war?.id||'',war?.opponent_type||war?.enemy_type||war?.kind||''].join('|')}
    hpState(war){const enemy=num(war?.opponent_hp),enemyMax=num(war?.opponent_hp_max),ours=num(war?.our_hp),oursMax=num(war?.our_hp_max);return {enemy,enemyMax,ours,oursMax}}
    ingest(war){
      if(!war){this.reset();return {reset:true,initial:false,events:[],state:null}}
      const key=this.identity(war),state=this.hpState(war);
      if(!this.prev||key!==this.key){this.prev={...state};this.key=key;return {reset:false,initial:true,events:[],state}}
      const events=[];
      if(state.enemyMax>0&&state.enemyMax===this.prev.enemyMax&&state.enemy!=null&&this.prev.enemy!=null&&state.enemy<this.prev.enemy)events.push({type:'attack',attacker:'ours',defender:'enemy',damage:Math.max(0,this.prev.enemy-state.enemy),remainingHp:state.enemy,maxHp:state.enemyMax,snapshot:{...war}});
      if(state.oursMax>0&&state.oursMax===this.prev.oursMax&&state.ours!=null&&this.prev.ours!=null&&state.ours<this.prev.ours)events.push({type:'attack',attacker:'enemy',defender:'ours',damage:Math.max(0,this.prev.ours-state.ours),remainingHp:state.ours,maxHp:state.oursMax,snapshot:{...war}});
      const healed=(state.enemy!=null&&this.prev.enemy!=null&&state.enemy>this.prev.enemy)||(state.ours!=null&&this.prev.ours!=null&&state.ours>this.prev.ours);
      this.prev={...state};
      return {reset:false,initial:false,events,state,forceSync:healed||events.length===0};
    }
  }
  w.TopKingBattleCore=w.TopKingBattleCore||{};
  w.TopKingBattleCore.WarEventAdapter=WarEventAdapter;
})(window);
