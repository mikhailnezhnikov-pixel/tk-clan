(function(w){
  'use strict';
  class BattleAnimator{
    constructor({gsap,scene,effects,onContact}){
      this.gsap=gsap;
      this.scene=scene;
      this.effects=effects;
      this.onContact=onContact||(()=>{});
      this.idleTweens=new Map();
      this.startIdle(scene.ours,0);
      this.startIdle(scene.enemy,.42);
    }
    stopIdle(fighter){
      if(!fighter)return;
      const tween=this.idleTweens.get(fighter);
      if(tween){tween.kill();this.idleTweens.delete(fighter)}
      this.gsap.killTweensOf(fighter.pose);
      this.gsap.killTweensOf(fighter.pose?.scale);
    }
    startIdle(fighter,delay=0){
      if(!fighter?.pose)return;
      this.stopIdle(fighter);
      fighter.setState('idle');
      fighter.resetPose();
      const dir=fighter.side==='left'?1:-1;
      const duration=fighter.side==='left'?1.45:1.62;
      const tl=this.gsap.timeline({repeat:-1,yoyo:true,delay});
      tl.to(fighter.pose,{y:-6,rotation:dir*.006,duration,ease:'sine.inOut'},0)
        .to(fighter.pose.scale,{x:1.012,y:.988,duration,ease:'sine.inOut'},0);
      this.idleTweens.set(fighter,tl);
    }
    play(event){
      return new Promise(resolve=>{
        const {gsap,scene}=this;
        const attacker=event.attacker==='enemy'?scene.enemy:scene.ours;
        const defender=event.attacker==='enemy'?scene.ours:scene.enemy;
        if(!attacker||!defender){this.onContact(event);resolve();return}

        this.stopIdle(attacker);
        this.stopIdle(defender);
        gsap.killTweensOf(attacker.container);
        gsap.killTweensOf(defender.container);
        attacker.reset();
        defender.reset();

        const dir=event.attacker==='enemy'?-1:1;
        const ax=attacker.base.x,ay=attacker.base.y;
        const dx=defender.base.x,dy=defender.base.y;
        const gap=Math.abs(dx-ax);
        const travel=Math.max(72,Math.min(126,gap*.27));
        const contactX=ax+dir*travel;
        const knockback=dir*38;

        const tl=gsap.timeline({
          onComplete:()=>{
            attacker.reset();
            defender.reset();
            this.startIdle(attacker,0);
            this.startIdle(defender,.28);
            resolve();
          }
        });

        // Wind-up: character compresses slightly before the strike.
        tl.to(attacker.pose,{y:2,rotation:-dir*.012,duration:.12,ease:'power2.in'},0)
          .to(attacker.pose.scale,{x:.975,y:1.025,duration:.12,ease:'power2.in'},0)

          // Attack frame + lunge. Only the fighter moves; arena/UI stay fixed.
          .call(()=>attacker.setState('attack'),null,.12)
          .to(attacker.container,{x:contactX,y:ay-5,rotation:dir*.022,duration:.30,ease:'power3.inOut'},.12)
          .to(attacker.pose,{y:-2,rotation:dir*.018,duration:.24,ease:'power3.out'},.16)
          .to(attacker.pose.scale,{x:1.03,y:.985,duration:.22,ease:'power3.out'},.16)

          // Contact: defender switches to hit pose and recoils.
          .call(()=>{
            defender.setState('hit');
            this.onContact(event);
          },null,.42)
          .to(defender.container,{x:dx+knockback,y:dy+5,rotation:dir*.045,duration:.12,ease:'power4.out'},.42)
          .to(defender.pose,{y:-3,rotation:dir*.035,duration:.12,ease:'power4.out'},.42)
          .to(defender.pose.scale,{x:.965,y:1.035,duration:.12,ease:'power4.out'},.42)

          // Short recovery from the hit.
          .to(defender.container,{x:dx+dir*14,y:dy,rotation:dir*.012,duration:.20,ease:'back.out(1.7)'},.54)
          .to(defender.pose,{y:0,rotation:0,duration:.20,ease:'back.out(1.7)'},.54)
          .to(defender.pose.scale,{x:1,y:1,duration:.20,ease:'back.out(1.7)'},.54)

          // Attacker pulls back and both return to idle frames.
          .to(attacker.container,{x:ax+dir*18,y:ay,rotation:0,duration:.20,ease:'power2.out'},.56)
          .call(()=>{attacker.setState('idle');defender.setState('idle')},null,.70)
          .to(attacker.container,{x:ax,y:ay,duration:.30,ease:'back.out(1.4)'},.70)
          .to(defender.container,{x:dx,y:dy,rotation:0,duration:.26,ease:'power2.out'},.70)
          .to(attacker.pose,{y:0,rotation:0,duration:.22,ease:'power2.out'},.70)
          .to(attacker.pose.scale,{x:1,y:1,duration:.22,ease:'power2.out'},.70)
          .to({}, {duration:.10},.98);
      });
    }
    destroy(){
      for(const tween of this.idleTweens.values())tween.kill();
      this.idleTweens.clear();
      for(const fighter of [this.scene?.ours,this.scene?.enemy]){
        if(!fighter)continue;
        this.gsap.killTweensOf(fighter.container);
        this.gsap.killTweensOf(fighter.pose);
        this.gsap.killTweensOf(fighter.pose?.scale);
      }
    }
  }
  w.TopKingBattleCore=w.TopKingBattleCore||{};
  w.TopKingBattleCore.BattleAnimator=BattleAnimator;
})(window);
