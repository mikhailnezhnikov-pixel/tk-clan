(function(w){
  'use strict';
  class BattleEventQueue{
    constructor(runner){this.runner=runner||null;this.items=[];this.running=false;this.epoch=0}
    setRunner(runner){this.runner=runner}
    enqueue(event){if(!event)return;this.items.push(event);this.drain()}
    enqueueMany(events){for(const e of events||[])if(e)this.items.push(e);this.drain()}
    clear(){this.items.length=0;this.epoch++}
    async drain(){
      if(this.running||!this.runner)return;
      this.running=true;const epoch=this.epoch;
      try{while(this.items.length&&epoch===this.epoch){const event=this.items.shift();await this.runner(event)}}
      catch(err){console.error('[BattleEventQueue]',err)}
      finally{this.running=false;if(this.items.length&&epoch===this.epoch)this.drain()}
    }
  }
  w.TopKingBattleCore=w.TopKingBattleCore||{};
  w.TopKingBattleCore.BattleEventQueue=BattleEventQueue;
})(window);
