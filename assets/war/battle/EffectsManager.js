(function(w){
  'use strict';
  class EffectsManager{
    constructor({PIXI,gsap,world,overlay}){this.PIXI=PIXI;this.gsap=gsap;this.world=world;this.overlay=overlay;this.fx=new PIXI.Container();this.fx.label='Battle FX';overlay.addChild(this.fx)}
    impact({x,y,damage=0,accent=0xef4940}){
      const {PIXI,gsap}=this;
      const ring=new PIXI.Graphics().circle(0,0,18).fill({color:0xffffff,alpha:.92});ring.position.set(x,y);this.fx.addChild(ring);
      const slash=new PIXI.Graphics().roundRect(-95,-6,190,12,6).fill({color:0xffffff,alpha:.95});slash.position.set(x,y);slash.rotation=-.32;slash.scale.x=.2;this.fx.addChild(slash);
      const sparks=new PIXI.Container();sparks.position.set(x,y);this.fx.addChild(sparks);
      for(let i=0;i<14;i++){const p=new PIXI.Graphics().circle(0,0,2+(i%3)).fill({color:i%2?accent:0xffd477,alpha:.95});const a=(Math.PI*2*i)/14+(Math.random()-.5)*.25,d=55+Math.random()*95;p._dx=Math.cos(a)*d;p._dy=Math.sin(a)*d;sparks.addChild(p);gsap.to(p,{x:p._dx,y:p._dy,alpha:0,duration:.45+Math.random()*.2,ease:'power2.out'})}
      const label=new PIXI.Text({text:'−'+Math.max(0,Math.round(damage)).toLocaleString('ru-RU'),style:{fontFamily:'Arial, sans-serif',fontSize:32,fontWeight:'900',fill:0xffffff,stroke:{color:accent,width:5},dropShadow:{color:0x000000,blur:8,alpha:.8,distance:2}}});label.anchor.set(.5);label.position.set(x,y-72);this.fx.addChild(label);
      gsap.to(ring.scale,{x:4.8,y:4.8,duration:.34,ease:'power3.out'});gsap.to(ring,{alpha:0,duration:.34,ease:'power2.out'});gsap.to(slash.scale,{x:1.35,duration:.24,ease:'power4.out'});gsap.to(slash,{alpha:0,duration:.32,ease:'power2.out'});gsap.fromTo(label,{y:y-52,alpha:1},{y:y-120,alpha:0,duration:.85,ease:'power2.out'});
      const baseX=this.world.x,baseY=this.world.y;
      gsap.timeline({onComplete:()=>{this.world.position.set(baseX,baseY);setTimeout(()=>{ring.destroy();slash.destroy();sparks.destroy({children:true});label.destroy()},30)}}).to(this.world,{x:baseX+9,y:baseY-5,duration:.045}).to(this.world,{x:baseX-8,y:baseY+4,duration:.045}).to(this.world,{x:baseX+5,y:baseY-2,duration:.045}).to(this.world,{x:baseX,y:baseY,duration:.06});
    }
    clear(){this.fx.removeChildren().forEach(c=>c.destroy?.({children:true}))}
  }
  w.TopKingBattleCore=w.TopKingBattleCore||{};
  w.TopKingBattleCore.EffectsManager=EffectsManager;
})(window);
