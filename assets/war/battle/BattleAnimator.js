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
    killMotion(fighter){
      if(!fighter)return;
      this.gsap.killTweensOf(fighter.container);
      this.gsap.killTweensOf(fighter.pose);
      this.gsap.killTweensOf(fighter.pose?.scale);
      this.gsap.killTweensOf(fighter.motion);
      this.gsap.killTweensOf(fighter.motion?.scale);
      this.gsap.killTweensOf(fighter.motion?.skew);
    }
    stopIdle(fighter){
      if(!fighter)return;
      const tween=this.idleTweens.get(fighter);
      if(tween){tween.kill();this.idleTweens.delete(fighter)}
      this.killMotion(fighter);
    }
    startIdle(fighter,delay=0){
      if(!fighter?.pose||!fighter?.motion)return;
      this.stopIdle(fighter);
      fighter.setState('idle',{duration:.18});
      fighter.resetMotion();
      const dir=fighter.side==='left'?1:-1;
      const duration=fighter.side==='left'?1.46:1.62;
      const tl=this.gsap.timeline({repeat:-1,yoyo:true,delay});
      tl.to(fighter.pose,{y:-6,rotation:dir*.005,duration,ease:'sine.inOut'},0)
        .to(fighter.pose.scale,{x:1.008,y:.994,duration,ease:'sine.inOut'},0)
        .to(fighter.motion,{y:-1.5,rotation:dir*.010,duration,ease:'sine.inOut'},0)
        .to(fighter.motion.scale,{x:1.020,y:.986,duration,ease:'sine.inOut'},0)
        .to(fighter.motion.skew,{x:dir*.012,duration,ease:'sine.inOut'},0);
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
        attacker.resetMotion();
        defender.resetMotion();
        attacker.setState('idle',{immediate:true});
        defender.setState('idle',{immediate:true});

        const dir=event.attacker==='enemy'?-1:1;
        const ax=attacker.base.x,ay=attacker.base.y;
        const dx=defender.base.x,dy=defender.base.y;
        const gap=Math.abs(dx-ax);
        const travel=Math.max(78,Math.min(138,gap*.29));
        const contactX=ax+dir*travel;
        const knockback=dir*40;

        const tl=gsap.timeline({
          onComplete:()=>{
            attacker.resetMotion();
            defender.resetMotion();
            attacker.setState('idle',{duration:.18});
            defender.setState('idle',{duration:.18});
            this.startIdle(attacker,0);
            this.startIdle(defender,.28);
            resolve();
          }
        });

        // Anticipation: continuous body compression and lean before the strike.
        tl.to(attacker.pose,{y:2,rotation:-dir*.010,duration:.11,ease:'power2.in'},0)
          .to(attacker.motion,{x:-dir*3,y:2,rotation:-dir*.035,duration:.11,ease:'power2.in'},0)
          .to(attacker.motion.scale,{x:.958,y:1.035,duration:.11,ease:'power2.in'},0)
          .to(attacker.motion.skew,{x:-dir*.030,duration:.11,ease:'power2.in'},0)

          // Blend into attack pose while the same character keeps moving.
          .call(()=>attacker.setState('attack',{duration:.10}),null,.10)
          .to(attacker.container,{x:contactX,y:ay-5,rotation:dir*.020,duration:.31,ease:'power3.inOut'},.10)
          .to(attacker.pose,{y:-3,rotation:dir*.012,duration:.25,ease:'power3.out'},.14)
          .to(attacker.motion,{x:dir*7,y:-3,rotation:dir*.055,duration:.25,ease:'power3.out'},.14)
          .to(attacker.motion.scale,{x:1.045,y:.970,duration:.23,ease:'power3.out'},.14)
          .to(attacker.motion.skew,{x:dir*.042,duration:.23,ease:'power3.out'},.14)

          // Contact: HP callback fires once, exactly when the visual hit lands.
          .call(()=>{
            defender.setState('hit',{duration:.08});
            this.onContact(event);
          },null,.42)
          .to(defender.container,{x:dx+knockback,y:dy+5,rotation:dir*.042,duration:.12,ease:'power4.out'},.42)
          .to(defender.pose,{y:-3,rotation:dir*.018,duration:.12,ease:'power4.out'},.42)
          .to(defender.motion,{x:dir*5,y:-4,rotation:dir*.050,duration:.12,ease:'power4.out'},.42)
          .to(defender.motion.scale,{x:.950,y:1.045,duration:.12,ease:'power4.out'},.42)
          .to(defender.motion.skew,{x:dir*.035,duration:.12,ease:'power4.out'},.42)

          // Recovery is continuous; no static snap back.
          .to(defender.container,{x:dx+dir*14,y:dy,rotation:dir*.010,duration:.20,ease:'back.out(1.7)'},.54)
          .to(defender.pose,{y:0,rotation:0,duration:.20,ease:'back.out(1.7)'},.54)
          .to(defender.motion,{x:0,y:0,rotation:0,duration:.20,ease:'back.out(1.7)'},.54)
          .to(defender.motion.scale,{x:1,y:1,duration:.20,ease:'back.out(1.7)'},.54)
          .to(defender.motion.skew,{x:0,duration:.20,ease:'back.out(1.7)'},.54)

          .to(attacker.container,{x:ax+dir*18,y:ay,rotation:0,duration:.20,ease:'power2.out'},.56)
          .call(()=>{
            attacker.setState('idle',{duration:.16});
            defender.setState('idle',{duration:.16});
          },null,.68)
          .to(attacker.container,{x:ax,y:ay,duration:.30,ease:'back.out(1.4)'},.68)
          .to(defender.container,{x:dx,y:dy,rotation:0,duration:.26,ease:'power2.out'},.68)
          .to(attacker.pose,{y:0,rotation:0,duration:.22,ease:'power2.out'},.68)
          .to(attacker.motion,{x:0,y:0,rotation:0,duration:.22,ease:'power2.out'},.68)
          .to(attacker.motion.scale,{x:1,y:1,duration:.22,ease:'power2.out'},.68)
          .to(attacker.motion.skew,{x:0,duration:.22,ease:'power2.out'},.68)
          .to({}, {duration:.10},.98);
      });
    }
    destroy(){
      for(const tween of this.idleTweens.values())tween.kill();
      this.idleTweens.clear();
      for(const fighter of [this.scene?.ours,this.scene?.enemy]){
        if(!fighter)continue;
        this.killMotion(fighter);
        fighter.destroy?.();
      }
    }
  }
  w.TopKingBattleCore=w.TopKingBattleCore||{};
  w.TopKingBattleCore.BattleAnimator=BattleAnimator;
})(window);
