const {test}=require('node:test');const assert=require('node:assert/strict');const vm=require('node:vm');const fs=require('node:fs');
const window={};const context=vm.createContext({window,console});
for(const file of ['WarEventAdapter','BattleEventQueue'])vm.runInContext(fs.readFileSync(`${__dirname}/${file}.js`,'utf8'),context);
const {WarEventAdapter,BattleEventQueue}=window.TopKingBattleCore;
const base={war_id:1,opponent:'Raider',opponent_hp:900,opponent_hp_max:1000,our_hp:800,our_hp_max:1000};
test('baseline, duplicate polling, both damage directions and snapshot ownership',()=>{
 const a=new WarEventAdapter();assert.equal(a.ingest(base).events.length,0);assert.equal(a.ingest({...base}).events.length,0);
 const next={...base,opponent_hp:765,our_hp:750};const events=a.ingest(next).events;
 assert.equal(events.length,2);assert.equal(events[0].attacker,'ours');assert.equal(events[0].damage,135);assert.equal(events[1].attacker,'enemy');assert.equal(events[1].damage,50);
 next.opponent_hp=0;assert.equal(events[0].snapshot.opponent_hp,765);
 assert.equal(a.ingest({...base,opponent_hp:765,our_hp:750}).events.length,0);
});
test('new identity, null HP and changed max do not fabricate attacks',()=>{
 const a=new WarEventAdapter();a.ingest(base);
 assert.equal(a.ingest({...base,opponent_hp:null}).events.length,0);
 assert.equal(a.ingest({...base,opponent_hp:500}).events.length,0);
 assert.equal(a.ingest({...base,war_id:2,opponent_hp:50}).events.length,0);
 assert.equal(a.ingest({...base,war_id:2,opponent_hp:20,opponent_hp_max:200}).events.length,0);
 a.reset();assert.equal(a.ingest(base).initial,true);
});
test('queue drains serially and resumes a new epoch after cancellation',async()=>{
 let release;const seen=[];const q=new BattleEventQueue(async e=>{seen.push(e);if(e===1)await new Promise(r=>release=r)});
 q.enqueueMany([1,2]);assert.deepEqual(seen,[1]);q.clear();q.enqueueMany([3,4]);release();
 await new Promise(r=>setImmediate(r));assert.deepEqual(seen,[1,3,4]);assert.equal(q.running,false);
});
test('queue announces completion only after the last real attack',async()=>{
 let release;const seen=[];const q=new BattleEventQueue(async e=>{seen.push(e);await new Promise(r=>release=r)},()=>seen.push('settled'));
 q.enqueueMany([1,2]);assert.deepEqual(seen,[1]);release();await new Promise(r=>setImmediate(r));
 assert.deepEqual(seen,[1,2]);release();await new Promise(r=>setImmediate(r));
 assert.deepEqual(seen,[1,2,'settled']);
});
