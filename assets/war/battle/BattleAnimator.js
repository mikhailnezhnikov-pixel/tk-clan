(function(w){
  'use strict';
  class BattleAnimator{
    constructor({gsap,scene,effects,onContact}){this.gsap=gsap;this.scene=scene;this.effects=effects;this.onContact=onContact||(()=>{})}
    play(event){
      return new Promise(resolve=>{
        const {gsap,scene}=this,attacker=event.attacker==='enemy'?scene.enemy:scene.ours,defender=event.attacker==='enemy'?scene.ours:scene.enemy;
        if(!attacker||!defender){this.onContact(event);resolve();return}
        const dir=event.attacker==='enemy'?-1:1;attacker.reset();defender.reset();attacker.setState('idle');defender.setState('idle');
        const ax=attacker.base.x,ay=attacker.base.y,dx=defender.base.x,dy=defender.base.y,distance=Math.max(120,Math.abs(dx-ax)*.48),contactX=ax+dir*distance,impactX=(contactX+dx)/2,impactY=Math.min(ay,dy)-118;
        const tl=gsap.timeline({onComplete:()=>{attacker.reset();defender.reset();resolve()}});
        tl.call(()=>attacker.setState('idle'),null,0).to(attacker.container,{y:ay-8,scaleX:1.025,scaleY:.985,duration:.16,ease:'power2.out'},.12).call(()=>attacker.setState('attack'),null,.28).to(attacker.container,{x:contactX,y:ay-3,rotation:dir*.045,duration:.32,ease:'power4.in'},.30).call(()=>{defender.setState('hit');this.effects.impact({x:impactX,y:impactY,damage:event.damage,accent:scene.accent});this.onContact(event)},null,.61).to(defender.container,{x:dx+dir*64,y:dy+7,rotation:dir*.10,scaleX:1.04,scaleY:.96,duration:.16,ease:'power3.out'},.61).to(defender.container,{x:dx+dir*24,y:dy,rotation:dir*.025,scaleX:1,scaleY:1,duration:.28,ease:'back.out(1.5)'},.77).to(attacker.container,{x:ax+dir*18,y:ay,duration:.28,ease:'power2.out'},.78).call(()=>{attacker.setState('idle');defender.setState('idle')},null,1.02).to(attacker.container,{x:ax,y:ay,rotation:0,duration:.42,ease:'back.out(1.35)'},1.02).to(defender.container,{x:dx,y:dy,rotation:0,duration:.34,ease:'power2.out'},1.02).to({}, {duration:.34},1.36);
      })
    }
  }
  w.TopKingBattleCore=w.TopKingBattleCore||{};
  w.TopKingBattleCore.BattleAnimator=BattleAnimator;
})(window);
