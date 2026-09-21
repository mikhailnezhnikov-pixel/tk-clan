(function(w){
  'use strict';
  class Fighter{
    constructor({PIXI,textures,side='left',height=310,name=''}){this.PIXI=PIXI;this.textures=textures||{};this.side=side;this.height=height;this.name=name;this.container=new PIXI.Container();this.container.label='Fighter '+name;this.sprite=new PIXI.Sprite(this.textures.idle||PIXI.Texture.EMPTY);this.sprite.anchor.set(.5,1);this.container.addChild(this.sprite);this.state='idle';this.base={x:0,y:0};this.face=side==='left'?1:-1;this.applyTexture('idle')}
    applyTexture(state){const tex=this.textures[state]||this.textures.idle||null;this.state=state;if(!tex){this.sprite.visible=false;return}this.sprite.visible=true;this.sprite.texture=tex;const h=Math.max(1,tex.height||1),s=this.height/h;this.sprite.scale.set(s*this.face,s)}
    setState(state){this.applyTexture(state)}
    setTextures(textures){this.textures=textures||this.textures;this.applyTexture('idle')}
    setBase(x,y){this.base={x,y};this.container.position.set(x,y)}
    reset(){this.container.position.set(this.base.x,this.base.y);this.container.rotation=0;this.container.scale.set(1);this.container.alpha=1;this.applyTexture('idle')}
    get x(){return this.container.x} set x(v){this.container.x=v}
    get y(){return this.container.y} set y(v){this.container.y=v}
  }
  w.TopKingBattleCore=w.TopKingBattleCore||{};
  w.TopKingBattleCore.Fighter=Fighter;
})(window);
