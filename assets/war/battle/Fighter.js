(function(w){
  'use strict';
  class Fighter{
    constructor({PIXI,textures,side='left',height=310,name=''}){
      Object.assign(this,{PIXI,textures,side,height,name});
      this.container=new PIXI.Container();this.pose=new PIXI.Container();this.container.addChild(this.pose);
      this.base={x:0,y:0};this.face=side==='left'?1:-1;
      // One subdivided surface for every key pose. Geometry is reused and
      // deformed at render time; no new sprites or buffers in the ticker.
      this.surfaces={};this.surfaceList=[];this.rig={breath:0,lean:0,wind:0,strike:0,stagger:0};
      this.time=side==='left'?0:1.7;this.buildSurfaces();this.reset();
    }
    buildSurfaces(){
      for(const surface of Object.values(this.surfaces))this.pose.removeChild(surface.mesh).destroy({children:true});
      this.surfaces={};
      for(const [state,frame] of Object.entries(this.textures)){
        const mesh=new this.PIXI.MeshPlane({texture:frame.texture,verticesX:7,verticesY:9,autoResize:false});
        const buffer=mesh.geometry.getAttribute('aPosition').buffer;
        const original=new Float32Array(buffer.data);
        mesh.alpha=state==='idle'?1:0;
        this.pose.addChild(mesh);
        this.surfaces[state]={mesh,buffer,original,frame};
      }
      this.surfaceList=Object.values(this.surfaces);this.resize();
    }
    resize(){
      for(const {mesh,frame} of this.surfaceList){
        const s=this.height/frame.bodyHeight;
        mesh.scale.set(s*this.face,s);
        mesh.position.set(-frame.footX*s*this.face,-frame.footY*s);
      }
    }
    setTextures(textures){if(this.textures===textures)return;this.textures=textures;this.buildSurfaces();this.reset()}
    setBase(x,y){this.base.x=x;this.base.y=y;this.container.position.set(x,y)}
    setState(state){
      for(const [key,surface] of Object.entries(this.surfaces))surface.mesh.alpha=key===state?1:0;
      this.state=state;
    }
    blend(state,amount){
      const v=Math.max(0,Math.min(1,amount));
      for(const [key,surface] of Object.entries(this.surfaces))surface.mesh.alpha=key===state?v:key==='idle'?1-v:0;
      this.state=state;
    }
    // Anatomical regions move at different rates; soles remain at their base.
    // The same rig deforms idle, attack and hit poses at 60fps, with no
    // animation of the arena or UI.
    tick(seconds,reduced){
      const rig=this.rig;
      if(!reduced&&this.state==='idle'){
        this.time+=seconds;
        rig.breath=Math.sin(this.time*2.6);
        rig.lean=Math.sin(this.time*1.5);
      }else if(reduced){rig.breath=0;rig.lean=0}
      for(const {buffer,original,frame,mesh} of this.surfaceList){
        if(mesh.alpha<=0)continue;
        const data=buffer.data,W=frame.texture.width,H=frame.texture.height,fx=frame.footX;
        for(let i=0;i<data.length;i+=2){
          const x=original[i],y=original[i+1],v=y/H;
          const top=Math.max(0,1-v),torso=Math.max(0,1-Math.abs(v-.48)*3.5);
          const sway=top*top*(rig.lean*1.8+rig.wind*7+rig.strike*11-rig.stagger*9);
          const breathe=(x-fx)*torso*rig.breath*.008;
          const cape=Math.max(0,(fx-x)/W)*Math.max(0,v-.35)*Math.sin(this.time*3+v*7)*2;
          data[i]=x+sway+breathe+cape;
          data[i+1]=y-torso*rig.breath*1.3-top*rig.wind*3-top*rig.strike*4+top*rig.stagger*4;
        }
        buffer.update();
      }
    }
    resetPose(){this.pose.position.set(0,0);this.pose.rotation=0;this.pose.scale.set(1);Object.assign(this.rig,{wind:0,strike:0,stagger:0})}
    reset(){this.container.position.set(this.base.x,this.base.y);this.container.rotation=0;this.container.alpha=1;this.resetPose();this.setState('idle')}
    destroy(){for(const {mesh} of this.surfaceList)this.pose.removeChild(mesh).destroy({children:true});this.surfaces={};this.surfaceList=[]}
  }
  w.TopKingBattleCore=w.TopKingBattleCore||{};w.TopKingBattleCore.Fighter=Fighter;
})(window);
