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
        this.gsap.killTweensOf(f.container);this.gsap.killTweensOf(f.rig);
        this.gsap.killTweensOf(f.pose);f.reset();
      }
    }
    play(event){
      if(this.destroyed)return Promise.resolve({cancelled:true});this.cancel();
      const a=event.attacker==='enemy'?this.scene.enemy:this.scene.ours;
      const d=event.attacker==='enemy'?this.scene.ours:this.scene.enemy;
      const dir=a.face,small=this.scene.width<600,reduced=this.motion.matches;
      const travel=reduced?0:Math.min(a.height*(small?.09:.19),this.scene.width*(small?.045:.06));
      const recoil=reduced?0:Math.min(d.height*.045,this.scene.width*.025);
      return new Promise(resolve=>{
        let contacted=false;
        const contact=()=>{if(contacted)return;contacted=true;this.onContact(event)};
        const active={resolve,timeline:null,contact};this.active=active;
        const finish=()=>{if(this.active!==active)return;this.active=null;a.reset();d.reset();resolve({cancelled:false})};
        const tl=this.gsap.timeline({onComplete:finish});active.timeline=tl;
        const t=reduced?.12:1;
        // The surface itself moves continuously. The two key poses blend over
        // short intervals so there is no abrupt texture cut.
        const blendA={value:0},blendD={value:0};
        tl.to(a.rig,{wind:1,duration:.16*t,ease:'power2.in'},0)
          .to(a.pose,{rotation:-dir*.014,duration:.16*t},0)
          .to(blendA,{value:1,duration:.11*t,onUpdate:()=>a.blend('attack',blendA.value)},.12*t)
          .to(a.rig,{wind:0,strike:1,duration:.18*t,ease:'power3.in'},.16*t)
          .to(a.container,{x:a.base.x+dir*travel,duration:.19*t,ease:'power3.in'},.16*t)
          .call(()=>{contact();d.blend('hit',.01)},null,.35*t)
          .to(blendD,{value:1,duration:.10*t,onUpdate:()=>d.blend('hit',blendD.value)},.35*t)
          .to(d.rig,{stagger:1,duration:.1*t},.35*t)
          .to(d.container,{x:d.base.x+dir*recoil,duration:.1*t},.35*t)
          .to(a.rig,{strike:0,duration:.3*t},.45*t)
          .to(a.container,{x:a.base.x,duration:.32*t,ease:'power2.out'},.47*t)
          .to(blendA,{value:0,duration:.25*t,onUpdate:()=>a.blend('attack',blendA.value)},.53*t)
          .to(d.rig,{stagger:0,duration:.28*t},.50*t)
          .to(d.container,{x:d.base.x,duration:.28*t,ease:'power2.out'},.50*t)
          .to(blendD,{value:0,duration:.26*t,onUpdate:()=>d.blend('hit',blendD.value)},.54*t)
          .to(a.pose,{rotation:0,duration:.3*t},.55*t)
          .to({}, {duration:.04*t},.82*t);
      });
    }
    destroy(){this.destroyed=true;this.motion.removeEventListener('change',this.motionHandler);this.cancel()}
  }
  w.TopKingBattleCore=w.TopKingBattleCore||{};w.TopKingBattleCore.BattleAnimator=BattleAnimator;
})(window);
