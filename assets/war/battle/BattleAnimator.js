(function(w){
  'use strict';
  class BattleAnimator{
    constructor({gsap,scene,onContact}){
      Object.assign(this,{gsap,scene,onContact});this.active=null;this.destroyed=false;
      this.motion=w.matchMedia('(prefers-reduced-motion: reduce)');
      this.motionHandler=()=>{this.cancel(true);this.scene.ours.reset();this.scene.enemy.reset()};
      this.motion.addEventListener('change',this.motionHandler);
    }
    cancel(deliverContact=false){
      const active=this.active;this.active=null;
      if(active){active.timeline.kill();if(deliverContact)active.contact();active.resolve({cancelled:true})}
      for(const f of [this.scene.ours,this.scene.enemy]){
        this.gsap.killTweensOf(f.container);this.gsap.killTweensOf(f.motion);
        this.gsap.killTweensOf(f.pose);f.reset();
      }
    }
    play(event){
      if(this.destroyed)return Promise.resolve({cancelled:true});this.cancel();
      const a=event.attacker==='enemy'?this.scene.enemy:this.scene.ours;
      const d=event.attacker==='enemy'?this.scene.ours:this.scene.enemy;
      const dir=a.face,small=this.scene.width<600,reduced=this.motion.matches;
      const travel=reduced?0:Math.min(a.height*(small?.105:.22),this.scene.width*(small?.048:.065));
      const recoil=reduced?0:Math.min(d.height*.045,this.scene.width*.025);
      return new Promise(resolve=>{
        let contacted=false;
        const contact=()=>{if(contacted)return;contacted=true;this.onContact(event)};
        const active={resolve,timeline:null,contact};this.active=active;
        const finish=()=>{if(this.active!==active)return;this.active=null;a.reset();d.reset();resolve({cancelled:false})};
        const tl=this.gsap.timeline({onComplete:finish});active.timeline=tl;
        const t=reduced?.12:1;
        a.setMotion('attack',0);
        tl.to(a.pose,{rotation:-dir*.022,duration:.16*t,ease:'power2.in'},0)
          .to(a.motion,{progress:1,duration:.75*t,ease:'none',onUpdate:()=>a.renderFrame()},0)
          .to(a.container,{x:a.base.x+dir*travel,duration:.18*t,ease:'power3.in'},.17*t)
          .call(()=>{contact();this.scene.impact(a,d);d.setMotion('hit',0)},null,.35*t)
          .to(d.motion,{progress:1,duration:.42*t,ease:'none',onUpdate:()=>d.renderFrame()},.35*t)
          .to(d.pose,{rotation:dir*.036,duration:.10*t},.35*t)
          .to(d.container,{x:d.base.x+dir*recoil,duration:.1*t},.35*t)
          .to(a.container,{x:a.base.x,duration:.34*t,ease:'power2.out'},.42*t)
          .to(d.container,{x:d.base.x,duration:.27*t,ease:'power2.out'},.49*t)
          .to(d.pose,{rotation:0,duration:.29*t},.48*t)
          .to(a.pose,{rotation:0,duration:.28*t},.49*t)
          .to({}, {duration:.07*t},.77*t);
      });
    }
    destroy(){this.destroyed=true;this.motion.removeEventListener('change',this.motionHandler);this.cancel()}
  }
  w.TopKingBattleCore=w.TopKingBattleCore||{};w.TopKingBattleCore.BattleAnimator=BattleAnimator;
})(window);
