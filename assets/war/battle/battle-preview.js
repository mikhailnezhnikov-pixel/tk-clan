// Explicit opt-in fixture. Never calls the war API or modifies server data.
(async function(){
  if(!new URLSearchParams(location.search).has('battlePreview'))return;
  await window.TopKingBattleV4.init();
  let fixture={war_id:'preview-1',opponent:'Backyard Mob',opponent_type:'clan',opponent_hp:900000,opponent_hp_max:900000,our_hp:900000,our_hp_max:900000};
  let contacts=0;
  const panel=document.createElement('section');panel.style.cssText='padding:16px;background:#171717;color:white;position:relative;z-index:100';
  const status=document.createElement('output');status.style.display='block';
  const report=(event)=>{status.textContent=`Preview only · enemy ${fixture.opponent_hp}/${fixture.opponent_hp_max} · ours ${fixture.our_hp}/${fixture.our_hp_max} · contacts ${contacts} · ${event||'idle'}`};
  const update=()=>{
    renderBattleScene(fixture,themeFor(fixture.opponent));
    document.getElementById('war-name').textContent=fixture.opponent;
    window.TopKingBattleV4.update({...fixture},{},{
      onHp:(hp,max)=>{applyBattleHp(hp,max);report('HP shown')},
      onEvent:event=>{contacts++;report(`${event.attacker} → ${event.defender}: ${event.damage}`)}
    });
    report('snapshot');
  };
  const button=(title,fn)=>{const b=document.createElement('button');b.textContent=title;b.style.cssText='padding:12px;margin:4px';b.onclick=fn;panel.append(b)};
  button('Top King attacks',()=>{fixture.opponent_hp-=1400;update()});
  button('Enemy attacks',()=>{fixture.our_hp-=2100;update()});
  button('Queue 4 hits',()=>{for(let i=0;i<4;i++){fixture.opponent_hp-=100+i;update()}});
  button('Unchanged poll',update);
  button('Switch bot / raider',()=>{fixture.opponent_type=fixture.opponent_type==='bot'?'clan':'bot';update()});
  button('Reset battle',()=>{window.TopKingBattleV4.update(null);fixture={...fixture,war_id:fixture.war_id+'x',opponent_hp:900000,our_hp:900000};update()});
  panel.append(status);document.querySelector('main').prepend(panel);update();
})();
