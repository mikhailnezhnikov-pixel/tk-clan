(function(w){
  'use strict';
  const CORE=()=>w.TopKingBattleCore||{};
  class BattleScene{
    constructor({PIXI,gsap,canvas,host}){this.PIXI=PIXI;this.gsap=gsap;this.canvas=canvas;this.host=host;this.app=null;this.world=null;this.overlay=null;this.ours=null;this.enemy=null;this.effects=null;this.animator=null;this.kind='clan';this.accent=0xef4940;this.ready=false;this.resizeHandler=()=>this.layout()}
    async init(onContact){
      const {PIXI}=this;this.app=new PIXI.Application();await this.app.init({canvas:this.canvas,resizeTo:this.host,backgroundAlpha:0,antialias:true,autoDensity:true,resolution:Math.min(devicePixelRatio||1,2)});
      this.world=new PIXI.Container();this.overlay=new PIXI.Container();this.app.stage.addChild(this.world,this.overlay);this.buildArena();
      const textures=await this.loadTextures();this.ours=new (CORE().Fighter)({PIXI,textures:textures.topking,side:'left',height:330,name:'Top King'});this.enemy=new (CORE().Fighter)({PIXI,textures:textures.raider,side:'right',height:330,name:'Opponent'});this.textureSets=textures;this.world.addChild(this.ours.container,this.enemy.container);
      this.effects=new (CORE().EffectsManager)({PIXI,gsap:this.gsap,world:this.world,overlay:this.overlay});this.animator=new (CORE().BattleAnimator)({gsap:this.gsap,scene:this,effects:this.effects,onContact});this.ready=true;this.host.classList.add('battle-stage-v4');this.layout();window.addEventListener('resize',this.resizeHandler,{passive:true});
    }
    async loadSet(base){const out={};for(const state of ['idle','attack','hit']){try{out[state]=await this.PIXI.Assets.load(base+'/'+state+'.webp?v=20260921-3')}catch(e){console.warn('[BattleScene] asset failed',base,state,e)}}return out}
    async loadTextures(){const [topking,raider,bot]=await Promise.all([this.loadSet('../assets/war/units/topking'),this.loadSet('../assets/war/units/raider'),this.loadSet('../assets/war/units/bot')]);return {topking,raider,bot}}
    buildArena(){
      const {PIXI}=this;const floor=new PIXI.Graphics().ellipse(0,0,300,54).fill({color:0x0d1218,alpha:.68});floor.label='Arena floor';this.floor=floor;this.world.addChild(floor);this.particles=new PIXI.Container();this.world.addChild(this.particles);
      for(let i=0;i<30;i++){const p=new PIXI.Graphics().circle(0,0,1+(i%3)).fill({color:i%4===0?0xe8b654:0xcbd4df,alpha:.28+(i%4)*.08});p._seed=i*17.3;this.particles.addChild(p)}
      this.app.ticker.add(()=>{const W=this.app.renderer.width/(this.app.renderer.resolution||1),H=this.app.renderer.height/(this.app.renderer.resolution||1),time=performance.now()/1000;for(let i=0;i<this.particles.children.length;i++){const p=this.particles.children[i];p.x=((p._seed*47+time*(5+i%4)*8)%Math.max(1,W));p.y=45+((p._seed*29+Math.sin(time*.7+i)*35)%Math.max(80,H-90))}});
    }
    setOpponentKind(kind){this.kind=kind==='bot'?'bot':'clan';if(this.enemy&&this.textureSets)this.enemy.setTextures(this.kind==='bot'?this.textureSets.bot:this.textureSets.raider)}
    setTheme(info){const raw=String(info?.accent||'#ef4940').replace('#',''),n=parseInt(raw,16);this.accent=Number.isFinite(n)?n:0xef4940}
    sync(war,info){if(!this.ready)return;this.setTheme(info);const name=String(war?.opponent||'').toLowerCase();this.setOpponentKind(/bot|бот|boss|босс/.test(name)?'bot':'clan');this.layout()}
    layout(){if(!this.ready)return;const W=this.host.clientWidth||900,H=this.host.clientHeight||420,y=Math.max(300,H*.78);this.ours.height=Math.min(350,H*.72);this.enemy.height=this.ours.height;this.ours.applyTexture(this.ours.state);this.enemy.applyTexture(this.enemy.state);this.ours.setBase(Math.max(190,W*.27),y);this.enemy.setBase(Math.min(W-190,W*.73),y);this.floor.position.set(W*.5,y+8);this.floor.scale.set(Math.max(.85,W/950),1)}
    async play(event){if(this.ready&&this.animator)await this.animator.play(event)}
    destroy(){window.removeEventListener('resize',this.resizeHandler);this.effects?.clear();this.app?.destroy(false,{children:true});this.ready=false}
  }
  w.TopKingBattleCore=w.TopKingBattleCore||{};
  w.TopKingBattleCore.BattleScene=BattleScene;
})(window);
