(function(w){
  'use strict';
  const CORE=()=>w.TopKingBattleCore||{};
  class BattleScene{
    constructor({PIXI,gsap,canvas,host}){Object.assign(this,{PIXI,gsap,canvasHost:canvas,host});this.ready=false;this.disposed=false;this.kind='clan';this.width=0;this.height=0;this.ownedTextures=[]}
    async init(onContact){
      const {PIXI}=this;this.app=new PIXI.Application();
      await this.app.init({backgroundAlpha:0,antialias:true,autoDensity:true,resolution:Math.min(w.devicePixelRatio||1,2)});
      if(this.disposed){this.app.destroy(true,{children:true});return}
      this.canvasHost.replaceChildren(this.app.canvas);
      this.world=new PIXI.Container();this.app.stage.addChild(this.world);this.buildArena();
      const textures=await this.loadTextures();
      if(this.disposed){this.disposeTextures();return}
      this.textureSets=textures;
      this.ours=new (CORE().Fighter)({PIXI,textures:textures.topking,side:'left',height:330,name:'Top King'});
      this.enemy=new (CORE().Fighter)({PIXI,textures:textures.raider,side:'right',height:330,name:'Opponent'});
      this.fx=new PIXI.Container();
      this.world.addChild(this.ours.container,this.enemy.container,this.fx);this.ready=true;this.layout();
      this.animator=new (CORE().BattleAnimator)({gsap:this.gsap,scene:this,onContact});
      this.tick=(ticker)=>{const dt=Math.min(.05,ticker.deltaMS/1000),reduced=this.animator.motion.matches;this.ours.tick(dt,reduced);this.enemy.tick(dt,reduced)};
      this.app.ticker.add(this.tick);
      this.host.classList.add('battle-stage-v4','battle-stage-v4-ready');
      this.observer=new ResizeObserver(()=>this.layout());this.observer.observe(this.host);
    }
    async image(url){
      const image=new Image();image.src=url;await image.decode();return image;
    }
    async loadTextures(){
      const {PIXI}=this;
      const images=await Promise.all(['topking-motion-v5.webp','raider-motion-v5.webp','bot-motion-v5.webp'].map(file=>this.image('../assets/war/units/'+file+'?v=20260923-5')));
      if(this.disposed)return {};
      const make=(image)=>{
        const atlas=PIXI.Texture.from(image);this.ownedTextures.push(atlas);
        const frames=[];
        for(let i=0;i<36;i++){
          const texture=new PIXI.Texture({source:atlas.source,frame:new PIXI.Rectangle(i%6*480,Math.floor(i/6)*320,480,320)});
          this.ownedTextures.push(texture);frames.push(texture);
        }
        return {idle:frames.slice(0,16),attack:frames.slice(16,28),hit:frames.slice(28)};
      };
      return {topking:make(images[0]),raider:make(images[1]),bot:make(images[2])};
    }
    buildArena(){
      const {PIXI}=this;this.floor=new PIXI.Graphics().ellipse(0,0,300,54).fill({color:0x0d1218,alpha:.68});this.world.addChild(this.floor);
      this.particles=new PIXI.Container();this.world.addChild(this.particles);
      // Preserve the ambient appearance without animating the background.
      for(let i=0;i<30;i++)this.particles.addChild(new PIXI.Graphics().circle(0,0,1+i%3).fill({color:i%4?0xcbd4df:0xe8b654,alpha:.28+i%4*.08}));
    }
    sync(war){
      if(!this.ready)return;
      const type=String(war?.opponent_type||war?.enemy_type||war?.kind||'')+' '+String(war?.opponent||'');
      const explicit=String(war?.opponent_type||war?.enemy_type||war?.kind||'').toLowerCase();
      const kind=/bot|boss|npc/i.test(explicit)?'bot':/clan|human/i.test(explicit)?'clan':/bot|boss|npc|бот|рейд|raid|страж|guardian|robot|drone/i.test(type)?'bot':'clan';
      if(kind!==this.kind){this.animator.cancel();this.kind=kind;this.enemy.setTextures(kind==='bot'?this.textureSets.bot:this.textureSets.raider)}
      this.host.dataset.opponentKind=war?kind:'none';
    }
    layout(){
      if(!this.ready)return;
      const W=this.host.clientWidth,H=this.host.clientHeight;if(!W||!H||W===this.width&&H===this.height)return;
      // Preserve an in-flight snapshot event through resize: complete its HP contact
      // exactly once and settle the pose, then let the queue continue.
      this.animator?.cancel(true);this.width=W;this.height=H;this.app.renderer.resize(W,H);
      const mobile=W<600,h=mobile?Math.min(H*.58,W*.43):Math.min(350,H*.67),y=mobile?Math.min(H-108,H*.73):Math.min(H-104,H*.76);
      this.ours.height=h;this.enemy.height=h;
      this.ours.setBase(W*(mobile?.24:.27),y);this.enemy.setBase(W*(mobile?.76:.73),y);
      this.ours.resize();this.enemy.resize();this.ours.reset();this.enemy.reset();
      this.floor.position.set(W*.5,y+8);this.floor.scale.set(W/950,1);
      this.particles.children.forEach((p,i)=>{p.x=((i*813.1)%W);p.y=35+(i*197.7)%Math.max(1,H-130)});
    }
    reset(){this.animator?.cancel();this.ours?.reset();this.enemy?.reset()}
    impact(attacker,defender){
      const flash=new this.PIXI.Graphics().circle(0,0,11).fill({color:0xffefc3,alpha:.78});
      flash.position.set(defender.base.x-attacker.face*defender.height*.27,defender.base.y-defender.height*.57);
      this.fx.addChild(flash);
      this.gsap.to(flash,{alpha:0,duration:.18,onComplete:()=>{flash.parent?.removeChild(flash);flash.destroy()}});
      this.gsap.to(flash.scale,{x:2.5,y:2.5,duration:.18});
    }
    async play(event){if(this.ready)return this.animator.play(event)}
    disposeTextures(){for(const texture of this.ownedTextures)texture.destroy(false);this.ownedTextures.length=0}
    destroy(){this.disposed=true;this.ready=false;this.observer?.disconnect();this.animator?.destroy();this.ours?.destroy();this.enemy?.destroy();if(this.app?.renderer)this.app.destroy(true,{children:true});this.disposeTextures();this.host.classList.remove('battle-stage-v4-ready','battle-stage-v4')}
  }
  w.TopKingBattleCore=w.TopKingBattleCore||{};w.TopKingBattleCore.BattleScene=BattleScene;
})(window);
