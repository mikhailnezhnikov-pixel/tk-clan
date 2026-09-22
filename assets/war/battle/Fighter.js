(function(w){
  'use strict';
  class Fighter{
    constructor({PIXI,gsap,textures,side='left',height=310,name=''}){
      this.PIXI=PIXI;
      this.gsap=gsap||w.gsap||null;
      this.textures=textures||{};
      this.side=side;
      this.height=height;
      this.name=name;
      this.container=new PIXI.Container();
      this.container.label='Fighter '+name;
      this.pose=new PIXI.Container();
      this.pose.label='Fighter pose '+name;
      this.motion=new PIXI.Container();
      this.motion.label='Fighter motion '+name;
      this.spriteA=new PIXI.Sprite(PIXI.Texture.EMPTY);
      this.spriteB=new PIXI.Sprite(PIXI.Texture.EMPTY);
      for(const sprite of [this.spriteA,this.spriteB]){
        sprite.anchor.set(.5,1);
        sprite.alpha=0;
        sprite.visible=false;
        this.motion.addChild(sprite);
      }
      this.pose.addChild(this.motion);
      this.container.addChild(this.pose);
      this.primary=this.spriteA;
      this.sprite=this.primary;
      this.state='idle';
      this.base={x:0,y:0};
      this.face=side==='left'?1:-1;
      this.setState('idle',{immediate:true});
      this.resetMotion();
    }
    textureFor(state){
      return this.textures[state]||this.textures.idle||null;
    }
    prepareSprite(sprite,state){
      const tex=this.textureFor(state);
      if(!tex){sprite.visible=false;sprite.alpha=0;return false}
      sprite.texture=tex;
      const h=Math.max(1,tex.height||1),s=this.height/h;
      sprite.scale.set(s*this.face,s);
      sprite.visible=true;
      return true;
    }
    setState(state,options={}){
      const tex=this.textureFor(state);
      this.state=state;
      if(!tex){
        this.spriteA.visible=false;this.spriteB.visible=false;
        this.spriteA.alpha=0;this.spriteB.alpha=0;
        return;
      }
      const immediate=options.immediate===true||!this.gsap;
      const duration=Number.isFinite(Number(options.duration))?Math.max(0,Number(options.duration)):.12;
      const current=this.primary||this.spriteA;
      const next=current===this.spriteA?this.spriteB:this.spriteA;
      this.gsap?.killTweensOf(this.spriteA);
      this.gsap?.killTweensOf(this.spriteB);
      if(immediate||duration===0){
        this.prepareSprite(current,state);
        current.alpha=1;
        next.alpha=0;
        next.visible=false;
        this.primary=current;
        this.sprite=current;
        return;
      }
      this.prepareSprite(next,state);
      next.alpha=0;
      current.visible=true;
      this.primary=next;
      this.sprite=next;
      this.gsap.to(current,{alpha:0,duration,ease:'sine.out',onComplete:()=>{current.visible=false}});
      this.gsap.to(next,{alpha:1,duration,ease:'sine.out'});
    }
    applyTexture(state){this.setState(state,{immediate:true})}
    setTextures(textures){this.textures=textures||this.textures;this.setState('idle',{immediate:true})}
    setBase(x,y){this.base={x,y};this.container.position.set(x,y)}
    resetMotion(){
      this.pose.position.set(0,0);
      this.pose.rotation=0;
      this.pose.scale.set(1);
      this.pose.alpha=1;
      this.motion.position.set(0,0);
      this.motion.rotation=0;
      this.motion.scale.set(1);
      this.motion.skew.set(0,0);
      this.motion.alpha=1;
    }
    resetPose(){this.resetMotion()}
    reset(){
      this.container.position.set(this.base.x,this.base.y);
      this.container.rotation=0;
      this.container.scale.set(1);
      this.container.alpha=1;
      this.resetMotion();
      this.setState('idle',{immediate:true});
    }
    destroy(){
      this.gsap?.killTweensOf(this.spriteA);
      this.gsap?.killTweensOf(this.spriteB);
      this.gsap?.killTweensOf(this.pose);
      this.gsap?.killTweensOf(this.motion);
      this.gsap?.killTweensOf(this.motion.scale);
      this.gsap?.killTweensOf(this.motion.skew);
    }
    get x(){return this.container.x} set x(v){this.container.x=v}
    get y(){return this.container.y} set y(v){this.container.y=v}
  }
  w.TopKingBattleCore=w.TopKingBattleCore||{};
  w.TopKingBattleCore.Fighter=Fighter;
})(window);
