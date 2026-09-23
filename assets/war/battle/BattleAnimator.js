(function(w){
  'use strict';
  class BattleAnimator{
    constructor({gsap,scene,onContact}){
      Object.assign(this,{gsap,scene,onContact});this.active=null;this.timer=null;this.fallTween=null;this.fallen=null;this.destroyed=false;
      this.atmosphere={active:false,ours:1,enemy:1,deferDefeat:false};this.turn=0;
      this.motion=w.matchMedia('(prefers-reduced-motion: reduce)');
      this.motionHandler=()=>{this.cancel(true);this.settle()};
      this.visibilityHandler=()=>{if(document.hidden)this.cancel(true);else this.settle()};
      this.motion.addEventListener('change',this.motionHandler);
      document.addEventListener('visibilitychange',this.visibilityHandler);
    }
    clearTimer(){if(this.timer!==null){clearTimeout(this.timer);this.timer=null}}
    cancel(deliverContact=false){
      this.clearTimer();
      const active=this.active;this.active=null;
      if(active){active.timeline.kill();if(deliverContact&&active.real)active.contact();active.resolve({cancelled:true})}
      if(this.fallTween){this.fallTween.kill();this.fallTween=null}
      this.fallen=null;
      for(const f of [this.scene.ours,this.scene.enemy]){
        this.gsap.killTweensOf(f.container);this.gsap.killTweensOf(f.motion);
        this.gsap.killTweensOf(f.pose);f.reset();
      }
    }
    setAtmosphere(next){
      const wasActive=this.atmosphere.active;
      this.atmosphere=next;
      if(!next.active){this.cancel();for(const f of [this.scene.ours,this.scene.enemy])f.setHealth(1);return}
      this.scene.ours.setHealth(next.ours);this.scene.enemy.setHealth(next.enemy);
      if(!wasActive){this.cancel();this.turn=0}
      if(!this.active)this.settle();
    }
    settle(){
      if(this.destroyed||!this.atmosphere.active||this.active)return;
      this.clearTimer();
      const {ours,enemy,deferDefeat}=this.atmosphere;
      // Wait for the queued HP contact before showing the final fall.
      const fallen=!deferDefeat&&(ours<=0?this.scene.ours:enemy<=0?this.scene.enemy:null);
      for(const f of [this.scene.ours,this.scene.enemy])if(f!==fallen){this.gsap.killTweensOf(f.pose);f.reset()}
      if(fallen){
        if(this.fallen===fallen)return;
        this.fallTween?.kill();this.fallen=fallen;
        fallen.setMotion('hit',.8);
        if(this.motion.matches){fallen.pose.rotation=fallen.face*1.1;return}
        this.fallTween=this.gsap.to(fallen.pose,{rotation:fallen.face*1.1,duration:.55,ease:'power2.inOut',onComplete:()=>{this.fallTween=null}});
        return;
      }
      this.fallen=null;this.schedule(this.turn?420:850);
    }
    queueDrained(){this.atmosphere.deferDefeat=false;this.settle()}
    schedule(delay){
      if(this.destroyed||this.timer!==null||this.active||!this.atmosphere.active||this.atmosphere.deferDefeat||
         this.atmosphere.ours<=0||this.atmosphere.enemy<=0||this.motion.matches||document.hidden)return;
      this.timer=setTimeout(()=>{this.timer=null;this.ambient()},delay);
    }
    ambient(){
      if(this.active||!this.atmosphere.active||this.motion.matches||document.hidden)return;
      const side=this.turn++%2?'enemy':'ours';this.perform({attacker:side},false);
    }
    play(event){
      if(this.destroyed)return Promise.resolve({cancelled:true});this.cancel();return this.perform(event,true);
    }
    perform(event,real){
      const a=event.attacker==='enemy'?this.scene.enemy:this.scene.ours;
      const d=event.attacker==='enemy'?this.scene.ours:this.scene.enemy;
      const dir=a.face,small=this.scene.width<600,reduced=this.motion.matches;
      const travel=reduced?0:Math.min(a.height*(small?.105:.22),this.scene.width*(small?.048:.065))*(1-a.fatigue*.22);
      const recoil=reduced?0:Math.min(d.height*.045,this.scene.width*.025);
      return new Promise(resolve=>{
        let contacted=false;
        const contact=()=>{if(contacted)return;contacted=true;if(real)this.onContact(event)};
        const active={resolve,timeline:null,contact,real};this.active=active;
        const finish=()=>{
          if(this.active!==active)return;
          this.active=null;a.reset();d.reset();resolve({cancelled:false});
          if(!real)this.schedule(360+Math.round(Math.max(a.fatigue,d.fatigue)*320));
        };
        const tl=this.gsap.timeline({onComplete:finish});active.timeline=tl;
        const t=reduced?.12:real?1:1+a.fatigue*.3;
        a.setMotion('attack',0);
        tl.to(a.pose,{rotation:-dir*.022,duration:.16*t,ease:'power2.in'},0)
          .to(a.motion,{progress:1,duration:.75*t,ease:'none',onUpdate:()=>a.renderFrame()},0)
          .to(a.container,{x:a.base.x+dir*travel,duration:.18*t,ease:'power3.in'},.17*t)
          .call(()=>{contact();this.scene.impact(a,d,!real);d.setMotion('hit',0)},null,.35*t)
          .to(d.motion,{progress:1,duration:.42*t,ease:'none',onUpdate:()=>d.renderFrame()},.35*t)
          .to(d.pose,{rotation:dir*.036,duration:.10*t},.35*t)
          .to(d.container,{x:d.base.x+dir*recoil,duration:.1*t},.35*t)
          .to(a.container,{x:a.base.x,duration:.34*t,ease:'power2.out'},.42*t)
          .to(d.container,{x:d.base.x,duration:.27*t,ease:'power2.out'},.49*t)
          .to(d.pose,{rotation:d.face*d.fatigue*.14,duration:.29*t},.48*t)
          .to(a.pose,{rotation:a.face*a.fatigue*.14,duration:.28*t},.49*t)
          .to({}, {duration:.07*t},.77*t);
      });
    }
    destroy(){this.destroyed=true;this.motion.removeEventListener('change',this.motionHandler);document.removeEventListener('visibilitychange',this.visibilityHandler);this.cancel()}
  }
  w.TopKingBattleCore=w.TopKingBattleCore||{};w.TopKingBattleCore.BattleAnimator=BattleAnimator;
})(window);
