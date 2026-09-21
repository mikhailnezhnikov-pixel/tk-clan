/* TopKing Clan Wars — PixiJS/GSAP battle renderer V2
 * Rendering only. Reads already-public war state from wars/index.html.
 * No game API calls and no backend writes.
 */
(function(){
  'use strict';

  const PIXI=window.PIXI;
  const gsap=window.gsap;
  const HOST_ID='battle-canvas';
  const STAGE_ID='battle-stage';
  const BG_URL='../assets/war/hamster-clan-battle-hq.webp';
  const ART_V3={
    topking:{
      idle:'../assets/war/units/topking/idle.webp?v=20260921-2',
      attack:'../assets/war/units/topking/attack.webp?v=20260921-2',
      hit:'../assets/war/units/topking/hit.webp?v=20260921-2'
    },
    raider:{
      idle:'../assets/war/units/raider/idle.webp?v=20260921-2',
      attack:'../assets/war/units/raider/attack.webp?v=20260921-2',
      hit:'../assets/war/units/raider/hit.webp?v=20260921-2'
    },
    bot:{
      idle:'../assets/war/units/bot/idle.webp?v=20260921-3',
      attack:'../assets/war/units/bot/attack.webp?v=20260921-3',
      hit:'../assets/war/units/bot/hit.webp?v=20260921-3'
    }
  };

  const ARCHETYPES=[
    {key:'raider', emblem:'☠', weapon:'axe',      primary:0xef4940, secondary:0x7a1515, metal:0xc9c4bb},
    {key:'iron',   emblem:'✦', weapon:'mace',     primary:0xbd6672, secondary:0x4a5360, metal:0xd7dde5},
    {key:'storm',  emblem:'⚡', weapon:'spear',    primary:0x64a6ff, secondary:0x264a78, metal:0xd9ecff},
    {key:'ember',  emblem:'♨', weapon:'sword',    primary:0xf39a35, secondary:0x7b4218, metal:0xffddb1},
    {key:'venom',  emblem:'◆', weapon:'daggers',  primary:0x8fd45f, secondary:0x3e6b2c, metal:0xc9f7ad},
    {key:'royal',  emblem:'♛', weapon:'halberd',  primary:0xd5a5ff, secondary:0x68468b, metal:0xf0ddff}
  ];

  const OVERRIDES={
    'шпана с окраины':'raider',
    'товарищи':'iron',
    'lad':'storm',
    'hamster pub':'ember',
    'top king':'royal',
    'top🏆king':'royal'
  };

  const OUR_STYLE={
    key:'topking',emblem:'♛',weapon:'sword',
    primary:0xe8b654,secondary:0x276fbd,metal:0xffe5a3,
    fur:0xc98951,furLight:0xf0cfaa
  };

  const reduced=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let app=null;
  let host=null;
  let stageEl=null;
  let world=null;
  let bgSprite=null;
  let atmosphere=null;
  let fightersLayer=null;
  let effectsLayer=null;
  let hudLayer=null;
  let ourFighter=null;
  let enemyFighter=null;
  let enemySignature='';
  let currentWar=null;
  let currentInfo=null;
  let ready=false;
  let initPromise=null;
  let loops=[];
  let resizeObserver=null;
  let sparks=[];
  let fog=[];
  let lastImpact=0;
  let ourArtEl=null;
  let enemyArtEl=null;
  let enemyArtKey='raider';
  let slashEl=null;
  let shotEl=null;
  let hitFlashEl=null;
  let hitLabelEl=null;
  let impactEl=null;
  const artPreload=[];

  function clamp(v,a,b){return Math.max(a,Math.min(b,v))}
  function normalize(value){return String(value||'').trim().toLowerCase().replace(/\s+/g,' ')}
  function hash(value){
    let h=2166136261;
    for(const ch of normalize(value)){h^=ch.codePointAt(0);h=Math.imul(h,16777619)}
    return h>>>0;
  }
  function hex(value,fallback){
    const s=String(value||'').trim().replace('#','');
    return /^[0-9a-f]{6}$/i.test(s)?parseInt(s,16):fallback;
  }
  function kindOf(war){
    const explicit=normalize(war?.opponent_type||war?.enemy_type||war?.kind||'');
    const name=normalize(war?.opponent||'');
    if(/bot|boss|npc|бот|босс/.test(explicit))return 'bot';
    return /(\bбот\b|\bbot\b|\bboss\b|\bnpc\b|рейд|raid|страж|guardian|robot|drone)/i.test(name)?'bot':'clan';
  }
  function enemyStyle(name,info,kind){
    if(kind==='bot'){
      return {
        key:'bot',emblem:'⬢',weapon:'cannon',
        primary:hex(info?.accent,0xef4940),secondary:hex(info?.accent2,0x592020),
        metal:0xd5e1ed,fur:0x56616c,furLight:0xbcc8d4
      };
    }
    const n=normalize(name);
    const key=OVERRIDES[n]||ARCHETYPES[hash(n)%ARCHETYPES.length].key;
    const base=ARCHETYPES.find(x=>x.key===key)||ARCHETYPES[0];
    return {
      ...base,
      primary:hex(info?.accent,base.primary),
      secondary:hex(info?.accent2,base.secondary),
      fur:0xb87848,furLight:0xe7c49d
    };
  }
  function rgb(color){
    return {
      r:((color>>16)&255)/255,
      g:((color>>8)&255)/255,
      b:(color&255)/255
    };
  }

  function gShape(draw){
    const g=new PIXI.Graphics();
    draw(g);
    return g;
  }
  function glowCircle(radius,color,alpha){
    return gShape(g=>g.circle(0,0,radius).fill({color,alpha}));
  }
  function ellipse(w,h,color,alpha){
    return gShape(g=>g.ellipse(0,0,w/2,h/2).fill({color,alpha}));
  }
  function line(x1,y1,x2,y2,width,color,alpha=1){
    return gShape(g=>g.moveTo(x1,y1).lineTo(x2,y2).stroke({width,color,alpha,cap:'round'}));
  }
  function poly(points,color,alpha=1,strokeColor=null,strokeWidth=0){
    return gShape(g=>{
      g.poly(points).fill({color,alpha});
      if(strokeColor!=null&&strokeWidth>0)g.stroke({color:strokeColor,width:strokeWidth,alpha:.9});
    });
  }

  function makeSword(style){
    const c=new PIXI.Container();
    const blade=poly([0,-5,93,-4,112,0,93,4,0,5],style.metal,.98,0xffffff,1);
    blade.x=12;
    const glow=line(18,0,105,0,3,style.primary,.75);
    const guard=line(10,-15,10,15,7,style.primary,1);
    const grip=line(-16,0,10,0,8,0x33261b,1);
    c.addChild(blade,glow,guard,grip);
    return c;
  }
  function makeAxe(style){
    const c=new PIXI.Container();
    const shaft=line(-42,0,58,0,9,0x5b3a25,1);
    const head=poly([48,-27,84,-18,94,0,84,18,48,27,60,0],style.metal,1,style.primary,2);
    c.addChild(shaft,head);
    return c;
  }
  function makeMace(style){
    const c=new PIXI.Container();
    c.addChild(line(-35,0,55,0,10,0x4a3626,1));
    const ball=glowCircle(23,style.metal,1);ball.x=70;
    const core=glowCircle(12,style.primary,.9);core.x=70;
    c.addChild(ball,core);
    return c;
  }
  function makeSpear(style){
    const c=new PIXI.Container();
    c.addChild(line(-58,0,76,0,7,0x6b5134,1));
    const tip=poly([74,-12,114,0,74,12],style.metal,1,style.primary,2);
    c.addChild(tip);
    return c;
  }
  function makeDaggers(style){
    const c=new PIXI.Container();
    const a=makeSword({...style});a.scale.set(.58);a.y=-12;a.rotation=-.16;
    const b=makeSword({...style});b.scale.set(.58);b.y=14;b.rotation=.16;
    c.addChild(a,b);
    return c;
  }
  function makeHalberd(style){
    const c=makeSpear(style);
    const hook=poly([58,-8,90,-34,82,-4],style.primary,.95,style.metal,1);
    c.addChild(hook);
    return c;
  }
  function makeCannon(style){
    const c=new PIXI.Container();
    const barrel=gShape(g=>g.roundRect(-18,-16,100,32,10).fill({color:0x2d3741}).stroke({color:style.primary,width:3}));
    const muzzle=gShape(g=>g.roundRect(65,-22,25,44,8).fill({color:style.metal}).stroke({color:style.primary,width:2}));
    const core=glowCircle(10,style.primary,.95);core.x=74;
    c.addChild(barrel,muzzle,core);
    return c;
  }
  function makeWeapon(style){
    if(style.weapon==='axe')return makeAxe(style);
    if(style.weapon==='mace')return makeMace(style);
    if(style.weapon==='spear')return makeSpear(style);
    if(style.weapon==='daggers')return makeDaggers(style);
    if(style.weapon==='halberd')return makeHalberd(style);
    if(style.weapon==='cannon')return makeCannon(style);
    return makeSword(style);
  }

  function makeHamster(style,side){
    const root=new PIXI.Container();
    root.label=side==='ours'?'TopKing warrior':'Opponent warrior';

    const aura=glowCircle(78,style.primary,.16);
    aura.scale.y=.46;aura.y=68;
    aura.blendMode='add';

    const shadow=ellipse(125,34,0x000000,.55);shadow.y=83;

    const cape=poly(
      side==='ours'
        ?[-45,-12,-70,67,-12,78,28,28]
        :[45,-12,70,67,12,78,-28,28],
      style.secondary,.88
    );
    cape.y=-4;

    const leftLeg=gShape(g=>g.roundRect(-35,48,25,46,10).fill({color:0x171b22}).stroke({color:style.metal,width:2}));
    const rightLeg=gShape(g=>g.roundRect(10,48,25,46,10).fill({color:0x171b22}).stroke({color:style.metal,width:2}));

    const body=gShape(g=>g.roundRect(-47,-20,94,86,25).fill({color:0x252b34}).stroke({color:style.metal,width:3}));
    const chest=poly([-34,-10,0,-27,34,-10,27,47,0,59,-27,47],style.secondary,.95,style.primary,2);
    const belt=gShape(g=>g.roundRect(-38,37,76,13,6).fill({color:0x1a1511}).stroke({color:style.primary,width:2}));
    const crest=glowCircle(10,style.primary,.92);crest.y=14;

    const armBack=gShape(g=>g.roundRect(-69,-7,29,66,13).fill({color:style.fur}).stroke({color:style.metal,width:2}));
    armBack.rotation=.14;
    const armFront=gShape(g=>g.roundRect(40,-7,29,66,13).fill({color:style.fur}).stroke({color:style.metal,width:2}));
    armFront.rotation=-.14;

    const earL=glowCircle(22,style.fur,.98);earL.x=-32;earL.y=-73;
    const earR=glowCircle(22,style.fur,.98);earR.x=32;earR.y=-73;
    const earLi=glowCircle(12,0xdca47f,.8);earLi.x=-32;earLi.y=-73;
    const earRi=glowCircle(12,0xdca47f,.8);earRi.x=32;earRi.y=-73;

    const head=glowCircle(48,style.fur,1);head.y=-50;
    const face=gShape(g=>g.ellipse(0,0,55,35).fill({color:style.furLight}));face.y=-36;
    const eyeL=glowCircle(5,0x0a0b0d,1);eyeL.x=-17;eyeL.y=-58;
    const eyeR=glowCircle(5,0x0a0b0d,1);eyeR.x=17;eyeR.y=-58;
    const eyeGlowL=glowCircle(2,0xffffff,.95);eyeGlowL.x=-18;eyeGlowL.y=-60;
    const eyeGlowR=glowCircle(2,0xffffff,.95);eyeGlowR.x=16;eyeGlowR.y=-60;
    const nose=glowCircle(5,0x41241d,1);nose.y=-38;

    const helmet=poly([-43,-65,-29,-91,0,-102,29,-91,43,-65,34,-52,-34,-52],0x242b34,.98,style.metal,2);
    const helmAccent=poly([-31,-70,0,-94,31,-70,21,-62,-21,-62],style.primary,.78);

    root.addChild(aura,shadow,cape,leftLeg,rightLeg,armBack,body,chest,belt,crest,armFront,earL,earR,earLi,earRi,head,face,eyeL,eyeR,eyeGlowL,eyeGlowR,nose,helmet,helmAccent);

    if(side==='ours'){
      const crown=poly([-36,-91,-29,-122,-10,-104,0,-132,12,-104,31,-122,36,-91],style.primary,1,style.metal,2);
      root.addChild(crown);
    }else{
      const plume=poly([-11,-102,0,-132,12,-102,7,-79,-7,-79],style.primary,.9);
      root.addChild(plume);
    }

    const weaponPivot=new PIXI.Container();
    const weapon=makeWeapon(style);
    weaponPivot.addChild(weapon);
    weaponPivot.x=side==='ours'?52:-52;
    weaponPivot.y=-2;
    weaponPivot.rotation=side==='ours'?-0.40:Math.PI+0.40;
    root.addChild(weaponPivot);

    root._weapon=weaponPivot;
    root._aura=aura;
    root._style=style;
    return root;
  }

  function makeRobot(style){
    const root=new PIXI.Container();
    root.label='Bot opponent';

    const aura=glowCircle(88,style.primary,.20);aura.scale.y=.43;aura.y=70;aura.blendMode='add';
    const shadow=ellipse(132,36,0x000000,.58);shadow.y=84;

    const legs=gShape(g=>{
      g.roundRect(-40,40,30,55,8).fill({color:0x1a2027}).stroke({color:style.metal,width:2});
      g.roundRect(10,40,30,55,8).fill({color:0x1a2027}).stroke({color:style.metal,width:2});
    });
    const body=gShape(g=>g.roundRect(-54,-24,108,90,18).fill({color:0x242d36}).stroke({color:style.primary,width:3}));
    const chest=gShape(g=>g.roundRect(-31,-3,62,48,14).fill({color:style.secondary}).stroke({color:style.metal,width:2}));
    const core=glowCircle(16,style.primary,1);core.y=20;core.blendMode='add';

    const head=gShape(g=>g.roundRect(-45,-89,90,62,15).fill({color:0x303a44}).stroke({color:style.metal,width:3}));
    const visor=gShape(g=>g.roundRect(-31,-70,62,17,8).fill({color:0x080b0e}).stroke({color:style.primary,width:2}));
    const eyeL=gShape(g=>g.roundRect(-21,-66,15,8,4).fill({color:style.primary}));eyeL.blendMode='add';
    const eyeR=gShape(g=>g.roundRect(6,-66,15,8,4).fill({color:style.primary}));eyeR.blendMode='add';
    const antenna=line(0,-89,0,-117,5,style.metal,1);
    const beacon=glowCircle(7,style.primary,1);beacon.y=-122;beacon.blendMode='add';

    const weaponPivot=new PIXI.Container();
    weaponPivot.addChild(makeCannon(style));
    weaponPivot.x=-52;weaponPivot.y=-5;weaponPivot.rotation=Math.PI+.12;

    root.addChild(aura,shadow,legs,body,chest,core,head,visor,eyeL,eyeR,antenna,beacon,weaponPivot);
    root._weapon=weaponPivot;root._aura=aura;root._style=style;
    return root;
  }

  function makeFighter(style,side,kind){
    return kind==='bot'?makeRobot(style):makeHamster(style,side);
  }

  function createAtmosphere(){
    const c=new PIXI.Container();
    for(let i=0;i<7;i++){
      const f=ellipse(280+Math.random()*260,65+Math.random()*55,0xc7d3df,.035+Math.random()*.045);
      f.x=Math.random()*900;f.y=180+Math.random()*280;
      f.blendMode='screen';
      f._vx=.08+Math.random()*.14;
      f._phase=Math.random()*Math.PI*2;
      fog.push(f);c.addChild(f);
    }
    for(let i=0;i<34;i++){
      const s=glowCircle(1.3+Math.random()*2.6,i%3===0?0xffffff:0xf5a542,.35+Math.random()*.6);
      s.blendMode='add';
      s._seed=Math.random();
      resetSpark(s,true);
      sparks.push(s);c.addChild(s);
    }
    return c;
  }

  function resetSpark(s,initial=false){
    const w=app?.renderer?.width||1000;
    const h=app?.renderer?.height||500;
    s.x=w*(.18+Math.random()*.64);
    s.y=initial?Math.random()*h:h*(.72+Math.random()*.18);
    s._vx=(-.25+Math.random()*.5);
    s._vy=-(.45+Math.random()*1.2);
    s.alpha=.15+Math.random()*.65;
    s.scale.set(.55+Math.random()*1.5);
  }

  function createImpactBurst(x,y,colorA,colorB){
    if(!effectsLayer||reduced)return;
    const flash=glowCircle(24,0xffffff,.95);
    flash.x=x;flash.y=y;flash.blendMode='add';
    effectsLayer.addChild(flash);
    gsap.to(flash.scale,{x:4.5,y:4.5,duration:.24,ease:'power2.out'});
    gsap.to(flash,{alpha:0,duration:.32,ease:'power2.out',onComplete:()=>flash.destroy()});

    for(let i=0;i<14;i++){
      const p=line(0,0,24+Math.random()*35,0,2+Math.random()*2,i%2?colorA:colorB,.85);
      p.x=x;p.y=y;p.rotation=Math.random()*Math.PI*2;p.blendMode='add';
      effectsLayer.addChild(p);
      const distance=45+Math.random()*80;
      gsap.to(p,{x:x+Math.cos(p.rotation)*distance,y:y+Math.sin(p.rotation)*distance,alpha:0,duration:.36+Math.random()*.28,ease:'power2.out',onComplete:()=>p.destroy()});
    }

    if(world){
      const ox=world.x,oy=world.y;
      gsap.killTweensOf(world);
      gsap.timeline()
        .to(world,{x:ox+5,y:oy-3,duration:.035})
        .to(world,{x:ox-6,y:oy+4,duration:.035})
        .to(world,{x:ox+3,y:oy-2,duration:.035})
        .to(world,{x:ox,y:oy,duration:.07});
    }
  }

  function preloadBattleArt(){
    for(const pack of Object.values(ART_V3)){
      for(const src of Object.values(pack)){
        const img=new Image();
        img.decoding='async';
        img.src=src;
        artPreload.push(img);
      }
    }
  }

  function setArt(side,state){
    const el=side==='ours'?ourArtEl:enemyArtEl;
    if(!el)return;
    const key=side==='ours'?'topking':enemyArtKey;
    const pack=ART_V3[key]||ART_V3.raider;
    const src=pack[state]||pack.idle;
    if(el.dataset.battleState===state&&el.getAttribute('src')===src)return;
    el.dataset.battleState=state;
    el.src=src;
  }

  function resetArt(){
    setArt('ours','idle');
    setArt('enemy','idle');
  }

  function resetVisiblePose(){
    if(ourArtEl)gsap.set(ourArtEl,{x:0,y:0,rotation:-1,scaleX:1,scaleY:1,opacity:1});
    if(enemyArtEl)gsap.set(enemyArtEl,{x:0,y:0,rotation:1,scaleX:-1,scaleY:1,opacity:1});
    if(slashEl)gsap.set(slashEl,{opacity:0,scaleX:.15,scaleY:1,x:0,y:0,rotation:-18});
    if(shotEl)gsap.set(shotEl,{opacity:0,x:0,y:0,scale:1});
    if(hitFlashEl)gsap.set(hitFlashEl,{opacity:0});
    if(hitLabelEl)gsap.set(hitLabelEl,{opacity:0,xPercent:-50,yPercent:-50,scale:.65,y:0});
    if(impactEl)gsap.set(impactEl,{opacity:0,scale:.2});
  }

  function visibleImpact(attacker){
    if(impactEl){
      gsap.killTweensOf(impactEl);
      gsap.set(impactEl,{opacity:1,scale:.25});
      gsap.to(impactEl,{opacity:0,scale:5,duration:.34,ease:'power2.out'});
    }
    if(hitFlashEl){
      gsap.killTweensOf(hitFlashEl);
      gsap.set(hitFlashEl,{opacity:.9});
      gsap.to(hitFlashEl,{opacity:0,duration:.28,ease:'power2.out'});
    }
    if(slashEl){
      gsap.killTweensOf(slashEl);
      gsap.set(slashEl,{opacity:1,scaleX:.18,scaleY:1,rotation:attacker==='ours'?-18:18,x:attacker==='ours'?-10:10});
      gsap.to(slashEl,{opacity:0,scaleX:1.65,duration:.28,ease:'power3.out'});
    }
    if(hitLabelEl){
      gsap.killTweensOf(hitLabelEl);
      gsap.set(hitLabelEl,{opacity:1,scale:.72,y:8});
      gsap.to(hitLabelEl,{opacity:0,scale:1.12,y:-24,duration:.48,ease:'power2.out'});
    }
    impact();
  }

  function fireBotShot(){
    if(!shotEl||!stageEl)return;
    const travel=Math.max(280,stageEl.clientWidth*.52);
    gsap.killTweensOf(shotEl);
    gsap.set(shotEl,{opacity:1,x:0,y:0,scale:.7});
    gsap.to(shotEl,{x:-travel,scale:1.25,duration:.34,ease:'power2.in',onComplete:()=>gsap.set(shotEl,{opacity:0})});
  }

  function clearLoops(){
    loops.forEach(t=>{try{t.kill()}catch(_){}});
    loops=[];
    if(ourFighter){gsap.killTweensOf(ourFighter);gsap.killTweensOf(ourFighter._weapon);gsap.killTweensOf(ourFighter._aura);}
    if(enemyFighter){gsap.killTweensOf(enemyFighter);gsap.killTweensOf(enemyFighter._weapon);gsap.killTweensOf(enemyFighter._aura);}
    if(ourArtEl)gsap.killTweensOf(ourArtEl);
    if(enemyArtEl)gsap.killTweensOf(enemyArtEl);
    for(const el of [slashEl,shotEl,hitFlashEl,hitLabelEl,impactEl])if(el)gsap.killTweensOf(el);
  }

  function setupLoops(){
    clearLoops();
    resetArt();
    resetVisiblePose();
    if(reduced||!currentWar||!ourFighter||!enemyFighter)return;

    const isBot=kindOf(currentWar)==='bot';
    const ourBaseX=ourFighter.x, ourBaseY=ourFighter.y;
    const enemyBaseX=enemyFighter.x, enemyBaseY=enemyFighter.y;
    const ourWeaponBase=ourFighter._weapon.rotation;
    const enemyWeaponBase=enemyFighter._weapon.rotation;

    const duel=gsap.timeline({repeat:-1,repeatDelay:.65});

    duel
      .call(()=>{resetArt();resetVisiblePose()},null,0)

      // Top King attacks.
      .call(()=>setArt('ours','attack'),null,.34)
      .to(ourFighter,{x:ourBaseX+26,y:ourBaseY-7,duration:.18,ease:'power2.out'},.36)
      .to(ourFighter._weapon,{rotation:ourWeaponBase+.72,duration:.18,ease:'power3.in'},.38)
      .to(ourFighter,{x:ourBaseX+122,y:ourBaseY-2,duration:.24,ease:'power4.in'},.56)
      .to(ourFighter._weapon,{rotation:ourWeaponBase+1.18,duration:.20,ease:'power4.in'},.56)
      .to(ourArtEl||{}, {x:168,y:-2,rotation:8,scaleX:1.08,scaleY:1.08,duration:.24,ease:'power4.in'},.56)
      .call(()=>{setArt('enemy','hit');visibleImpact('ours')},null,.80)
      .to(enemyFighter,{x:enemyBaseX+58,y:enemyBaseY+9,rotation:.10,duration:.14,ease:'power3.out'},.80)
      .to(enemyFighter._weapon,{rotation:enemyWeaponBase-.35,duration:.14,ease:'power3.out'},.80)
      .to(enemyFighter,{x:enemyBaseX+24,y:enemyBaseY+2,rotation:.03,duration:.24,ease:'back.out(1.5)'},.94)
      .to(ourFighter,{x:ourBaseX,y:ourBaseY,rotation:0,duration:.40,ease:'back.out(1.4)'},.96)
      .to(ourFighter._weapon,{rotation:ourWeaponBase,duration:.38,ease:'power2.out'},.96)
      .call(()=>{setArt('ours','idle');setArt('enemy','idle')},null,1.30)
      .to(enemyFighter,{x:enemyBaseX,y:enemyBaseY,rotation:0,duration:.22,ease:'power2.out'},1.28)
      .to(enemyFighter._weapon,{rotation:enemyWeaponBase,duration:.22,ease:'power2.out'},1.28)

      // Opponent answers.
      .call(()=>setArt('enemy','attack'),null,1.68)
      .to(enemyFighter,{x:enemyBaseX-24,y:enemyBaseY-6,duration:.18,ease:'power2.out'},1.70)
      .to(enemyFighter._weapon,{rotation:enemyWeaponBase-.65,duration:.18,ease:'power3.in'},1.72);

    if(isBot){
      duel
        .call(()=>fireBotShot(),null,1.90)
        .call(()=>{setArt('ours','hit');visibleImpact('enemy')},null,2.20);
    }else{
      duel
        .to(enemyFighter,{x:enemyBaseX-118,y:enemyBaseY-1,duration:.24,ease:'power4.in'},1.90)
        .to(enemyFighter._weapon,{rotation:enemyWeaponBase-1.10,duration:.20,ease:'power4.in'},1.90)
        .call(()=>{setArt('ours','hit');visibleImpact('enemy')},null,2.14);
    }

    duel
      .to(ourFighter,{x:ourBaseX-56,y:ourBaseY+8,rotation:-.10,duration:.15,ease:'power3.out'},2.14)
      .to(ourFighter,{x:ourBaseX-22,y:ourBaseY+2,rotation:-.03,duration:.24,ease:'back.out(1.4)'},2.29)
      .to(enemyFighter,{x:enemyBaseX,y:enemyBaseY,rotation:0,duration:.38,ease:'back.out(1.4)'},2.30)
      .to(enemyFighter._weapon,{rotation:enemyWeaponBase,duration:.36,ease:'power2.out'},2.30)
      .call(()=>{setArt('ours','idle');setArt('enemy','idle')},null,2.62)
      .to(ourFighter,{x:ourBaseX,y:ourBaseY,rotation:0,duration:.26,ease:'power2.out'},2.62)
      .to(ourFighter._weapon,{rotation:ourWeaponBase,duration:.26,ease:'power2.out'},2.62)
      .to({}, {duration:.82},2.88);

    loops.push(duel);

    const auraA=gsap.to(ourFighter._aura,{alpha:.34,scaleX:1.20,scaleY:.56,duration:1.1,yoyo:true,repeat:-1,ease:'sine.inOut'});
    const auraB=gsap.to(enemyFighter._aura,{alpha:.36,scaleX:1.18,scaleY:.54,duration:1.25,yoyo:true,repeat:-1,ease:'sine.inOut'});
    loops.push(auraA,auraB);
  }

  function impact(){
    const now=performance.now();
    if(now-lastImpact<250)return;
    lastImpact=now;
    const w=app?.renderer?.width||1000;
    const h=app?.renderer?.height||500;
    const colorA=OUR_STYLE.primary;
    const colorB=enemyFighter?enemyFighter._style.primary:0xef4940;
    createImpactBurst(w*.50,h*.54,colorA,colorB);
  }

  function healthIntensity(war){
    const eh=Number(war?.opponent_hp),em=Number(war?.opponent_hp_max);
    const oh=Number(war?.our_hp),om=Number(war?.our_hp_max);
    if(Number.isFinite(eh)&&Number.isFinite(em)&&em>0)return clamp(1-(eh/em),0,1);
    if(Number.isFinite(oh)&&Number.isFinite(om)&&om>0)return clamp(1-(oh/om),0,1);
    return .35;
  }

  function layout(){
    if(!app||!host||!world)return;
    const w=Math.max(320,app.renderer.width||host.clientWidth||1000);
    const h=Math.max(260,app.renderer.height||host.clientHeight||500);

    if(bgSprite&&bgSprite.texture){
      const tw=bgSprite.texture.width||w,th=bgSprite.texture.height||h;
      const scale=Math.max(w/tw,h/th)*1.06;
      bgSprite.scale.set(scale);
      bgSprite.x=w/2;bgSprite.y=h/2;
      bgSprite.anchor.set(.5);
    }

    if(ourFighter){
      const scale=clamp(Math.min(w/1100,h/560),.62,1.22);
      ourFighter.scale.set(scale);
      ourFighter.x=w*.22;ourFighter.y=h*.62;
    }
    if(enemyFighter){
      const scale=clamp(Math.min(w/1100,h/560),.62,1.22);
      enemyFighter.scale.set(-scale,scale);
      enemyFighter.x=w*.78;enemyFighter.y=h*.62;
    }

    setupLoops();
  }

  function rebuildEnemy(){
    if(!fightersLayer||!currentWar)return;
    const kind=kindOf(currentWar);
    const style=enemyStyle(currentWar.opponent,currentInfo,kind);
    enemyArtKey=kind==='bot'?'bot':'raider';
    const sig=kind+'|'+normalize(currentWar.opponent)+'|'+style.key+'|'+style.primary+'|'+style.secondary;
    if(sig===enemySignature&&enemyFighter)return;
    enemySignature=sig;

    if(enemyFighter){
      gsap.killTweensOf(enemyFighter);
      enemyFighter.destroy({children:true});
      enemyFighter=null;
    }
    enemyFighter=makeFighter(style,'enemy',kind);
    fightersLayer.addChild(enemyFighter);
    layout();
  }

  function ticker(){
    if(!app)return;
    const w=app.renderer.width||1000,h=app.renderer.height||500;
    const intensity=healthIntensity(currentWar);
    for(const f of fog){
      f.x+=f._vx*(.6+intensity*.8);
      f.y+=Math.sin(performance.now()/2200+f._phase)*.02;
      if(f.x>w+180)f.x=-180;
    }
    for(const s of sparks){
      s.x+=s._vx*(1+intensity*.6);
      s.y+=s._vy*(.8+intensity*.8);
      s.alpha-=.0015;
      if(s.y<20||s.alpha<=.03||s.x<-20||s.x>w+20)resetSpark(s,false);
    }
  }

  async function init(){
    if(ready)return true;
    if(initPromise)return initPromise;

    initPromise=(async()=>{
      host=document.getElementById(HOST_ID);
      stageEl=document.getElementById(STAGE_ID);
      ourArtEl=document.getElementById('battle-art-ours');
      enemyArtEl=document.getElementById('battle-art-enemy');
      impactEl=document.getElementById('battle-art-impact');
      slashEl=document.getElementById('battle-slash');
      shotEl=document.getElementById('battle-shot');
      hitFlashEl=document.getElementById('battle-hit-flash');
      hitLabelEl=document.getElementById('battle-hit-label');
      preloadBattleArt();
      if(!host||!stageEl||!PIXI||!gsap){
        stageEl?.classList.add('battle-v2-failed');
        return false;
      }

      app=new PIXI.Application();
      await app.init({
        resizeTo:host,
        backgroundAlpha:0,
        antialias:true,
        autoDensity:true,
        resolution:Math.min(window.devicePixelRatio||1,2),
        preference:'webgl'
      });
      app.canvas.setAttribute('aria-hidden','true');
      host.replaceChildren(app.canvas);

      world=new PIXI.Container();world.label='Battle world';
      atmosphere=createAtmosphere();atmosphere.label='Atmosphere';
      fightersLayer=new PIXI.Container();fightersLayer.label='Fighters';
      // V3 art characters are rendered by the HTML art layer; keep the procedural
      // Pixi fighters only as hidden timing rigs so their GSAP timeline continues
      // to drive impact particles/camera shake without double-drawing characters.
      // Keep the procedural fighters visible as the guaranteed live combat layer.
      // V3 raster art is an enhancement, never a single point of failure.
      fightersLayer.visible=true;
      effectsLayer=new PIXI.Container();effectsLayer.label='Impact effects';
      hudLayer=new PIXI.Container();hudLayer.label='Canvas HUD';
      world.addChild(atmosphere,fightersLayer,effectsLayer,hudLayer);
      app.stage.addChild(world);

      // V3 uses a clean procedural arena. The old illustrated battle image
      // looked like a second static fight behind the real characters.
      bgSprite=null;

      ourFighter=makeFighter(OUR_STYLE,'ours','clan');
      fightersLayer.addChild(ourFighter);

      app.ticker.add(ticker);
      resizeObserver=new ResizeObserver(()=>requestAnimationFrame(layout));
      resizeObserver.observe(host);

      ready=true;
      stageEl.classList.add('battle-v2-ready');
      if(currentWar)rebuildEnemy();
      layout();
      return true;
    })().catch(error=>{
      console.error('[TopKing Battle V2]',error);
      stageEl?.classList.add('battle-v2-failed');
      return false;
    });

    return initPromise;
  }

  async function update(war,info){
    currentWar=war||null;
    currentInfo=info||null;
    const ok=await init();
    if(!ok)return;
    if(!currentWar){
      clearLoops();
      resetArt();
      if(enemyFighter){enemyFighter.alpha=.28}
      if(ourFighter){ourFighter.alpha=.45}
      return;
    }
    if(ourFighter)ourFighter.alpha=1;
    rebuildEnemy();
    if(enemyFighter)enemyFighter.alpha=1;
    layout();
  }

  function destroy(){
    clearLoops();
    try{resizeObserver?.disconnect()}catch(_){}
    try{app?.destroy(true,{children:true,texture:false})}catch(_){}
    app=null;ready=false;initPromise=null;
  }

  window.TopKingBattleV2={init,update,destroy,version:'3.4.0-guaranteed-fighters'};
})();