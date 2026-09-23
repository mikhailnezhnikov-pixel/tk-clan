(function(w){
  'use strict';
  class Fighter{
    constructor({PIXI,textures,side='left',height=310,name=''}){
      Object.assign(this,{PIXI,textures,side,height,name});
      this.container=new PIXI.Container();this.pose=new PIXI.Container();this.container.addChild(this.pose);
      this.base={x:0,y:0};this.face=side==='left'?1:-1;
      this.surfaces={};this.parts=[];this.rig={breath:0,lean:0,wind:0,strike:0,stagger:0};
      this.time=side==='left'?0:1.7;this.buildSurfaces();this.reset();
    }
    buildSurfaces(){
      for(const part of this.parts){this.pose.removeChild(part.sprite);part.sprite.destroy();part.texture.destroy(false)}
      this.surfaces={};this.parts=[];
      for(const [state,frame] of Object.entries(this.textures)){
        const sections=[];
        const image=frame.texture,cut1=Math.round(image.height*.38),cut2=Math.round(image.height*.73);
        const cuts=[[0,cut1,'head'],[cut1,cut2,'torso'],[cut2,image.height,'legs']];
        for(const [start,end,region] of cuts){
          const texture=new this.PIXI.Texture({source:image.source,frame:new this.PIXI.Rectangle(image.frame.x,image.frame.y+start,image.width,end-start)});
          const sprite=new this.PIXI.Sprite(texture);sprite.anchor.set(frame.footX/image.width,1);
          sprite.alpha=state==='idle'?1:0;
          // Paint from legs upwards so moving pieces cover their seam.
          sections.push({sprite,texture,frame,start,end,region});
        }
        this.surfaces[state]=sections;
        for(const section of sections.slice().reverse())this.pose.addChild(section.sprite);
        this.parts.push(...sections);
      }
      this.resize();
    }
    resize(){
      for(const part of this.parts){
        const s=this.height/part.frame.bodyHeight;
        part.sprite.scale.set(s*this.face,s);
        part.sprite.position.set(0,(part.end-part.frame.footY)*s);
      }
    }
    setTextures(textures){if(this.textures===textures)return;this.textures=textures;this.buildSurfaces();this.reset()}
    setBase(x,y){this.base.x=x;this.base.y=y;this.container.position.set(x,y)}
    setState(state){for(const [key,sections] of Object.entries(this.surfaces))for(const part of sections)part.sprite.alpha=key===state?1:0;this.state=state}
    blend(state,amount){
      const v=Math.max(0,Math.min(1,amount));
      for(const [key,sections] of Object.entries(this.surfaces))for(const part of sections)part.sprite.alpha=key===state?v:key==='idle'?1-v:0;
      this.state=state;
    }
    // Independent head, chest and planted legs. All coordinates are set in
    // place; there are no new display objects or tweens in the render loop.
    tick(seconds,reduced){
      const rig=this.rig;
      if(!reduced&&this.state==='idle'){this.time+=seconds;rig.breath=Math.sin(this.time*2.6);rig.lean=Math.sin(this.time*1.5)}
      else if(reduced){rig.breath=0;rig.lean=0}
      for(const part of this.parts){
        if(part.sprite.alpha<=0)continue;
        const s=this.height/part.frame.bodyHeight,head=part.region==='head',torso=part.region==='torso';
        const sway=(rig.lean*1.8+rig.wind*5+rig.strike*10-rig.stagger*8)*s;
        part.sprite.position.x=(head?sway:torso?sway*.42:0)*this.face;
        part.sprite.position.y=(part.end-part.frame.footY)*s-(head?rig.breath*1.1:torso?rig.breath*.5:0)*s;
        part.sprite.rotation=(head?rig.lean*.009+rig.strike*.016-rig.stagger*.024:torso?rig.wind*.011+rig.strike*.016-rig.stagger*.012:0)*this.face;
        part.sprite.scale.y=s*(1+(head?rig.breath*.002:torso?rig.breath*.008:0));
      }
    }
    resetPose(){this.pose.position.set(0,0);this.pose.rotation=0;this.pose.scale.set(1);Object.assign(this.rig,{wind:0,strike:0,stagger:0})}
    reset(){this.container.position.set(this.base.x,this.base.y);this.container.rotation=0;this.container.alpha=1;this.resetPose();this.setState('idle')}
    destroy(){for(const part of this.parts){this.pose.removeChild(part.sprite);part.sprite.destroy();part.texture.destroy(false)}this.parts=[];this.surfaces={}}
  }
  w.TopKingBattleCore=w.TopKingBattleCore||{};w.TopKingBattleCore.Fighter=Fighter;
})(window);
