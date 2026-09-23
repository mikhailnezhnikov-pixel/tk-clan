(function(w){
  'use strict';
  // An offline atlas contains 16 idle, 12 attack and 8 hit drawings. Pixi
  // interpolates neighbouring drawings on each display refresh (usually 60 Hz).
  const FOOT_X=185/480, FOOT_Y=300/320, BODY_HEIGHT=260;
  class Fighter{
    constructor({PIXI,textures,side='left',height=310,name=''}){
      Object.assign(this,{PIXI,textures,side,height,name});
      this.container=new PIXI.Container();this.pose=new PIXI.Container();this.container.addChild(this.pose);
      this.base={x:0,y:0};this.face=side==='left'?1:-1;
      this.motion={progress:0};this.state='idle';this.time=side==='left'?0:1.1;
      this.front=new PIXI.Sprite(PIXI.Texture.EMPTY);this.back=new PIXI.Sprite(PIXI.Texture.EMPTY);
      for(const sprite of [this.front,this.back]){sprite.anchor.set(FOOT_X,FOOT_Y);this.pose.addChild(sprite)}
      this.resize();this.reset();
    }
    resize(){
      const s=this.height/BODY_HEIGHT;
      for(const sprite of [this.front,this.back])sprite.scale.set(s*this.face,s);
    }
    setTextures(textures){if(this.textures===textures)return;this.textures=textures;this.reset()}
    setBase(x,y){this.base.x=x;this.base.y=y;this.container.position.set(x,y)}
    setMotion(state,progress=0){this.state=state;this.motion.progress=Math.max(0,Math.min(1,progress));this.renderFrame()}
    renderFrame(){
      const frames=this.textures[this.state]||this.textures.idle;
      const phase=this.state==='idle'?(this.time/2.25%1)*frames.length:this.motion.progress*(frames.length-1);
      const index=Math.min(frames.length-1,Math.floor(phase));
      const next=this.state==='idle'?(index+1)%frames.length:Math.min(frames.length-1,index+1);
      const mix=phase-index;
      if(this.front.texture!==frames[index])this.front.texture=frames[index];
      if(this.back.texture!==frames[next])this.back.texture=frames[next];
      this.front.alpha=1;this.back.alpha=mix;
    }
    tick(seconds,reduced){if(this.state==='idle'&&!reduced)this.time+=seconds;this.renderFrame()}
    reset(){this.container.position.set(this.base.x,this.base.y);this.container.rotation=0;this.container.alpha=1;this.pose.rotation=0;this.setMotion('idle',0)}
    destroy(){this.front.destroy();this.back.destroy()}
  }
  w.TopKingBattleCore=w.TopKingBattleCore||{};w.TopKingBattleCore.Fighter=Fighter;
})(window);
