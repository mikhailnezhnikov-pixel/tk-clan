from pathlib import Path
import sys

target = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/HamsterKingMobile.user.js")
s = target.read_text(encoding="utf-8")

def need(old, label, count=1):
    actual = s.count(old)
    if actual != count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")

def rep(old, new, label, count=1):
    global s
    need(old, label, count)
    s = s.replace(old, new, count)

if "rumors-hunter-coordinator-kokkaras-v40-20260926-r4" in s:
    print("RUMORS_HUNTER_FULL_1_18_15_ALREADY_PRESENT")
    raise SystemExit(0)

rep(
    "// @version      1.18.14",
    "// @version      1.18.15\n"
    "// @release-note Слухи: полноценная «Охота за слухами» переведена на канон Kokkaras v40 из 5.3.22-ui-icons-pit-dim: распределение городов через HK coordinator, claim/lease/heartbeat, поиск 3/3 с радиусом 3 и city-policy, защита сигнатур карты, общие результаты Kokkaras+HK, live-статусы/история и переходы по найденным координатам. Старый блок «Сегодня» сохранён.",
    "metadata version"
)
rep("const BUILD_VERSION = '1.18.14';", "const BUILD_VERSION = '1.18.15';", "build version")

marker = "  const HK_RUMORS_SHARED_RESULTS_REV='rumors-shared-results-20260926-r2';"
rep(
    marker,
    marker + "\n"
    "  const HK_RUMORS_HUNTER_FULL_REV='rumors-hunter-coordinator-kokkaras-v40-20260926-r4';\n"
    "  const RUMOR_HUNTER_RADIUS=3;\n"
    "  const RUMOR_HUNTER_JACKPOTS=3;",
    "rumor constants"
)

state_anchor = """  let rumorAutoRefreshTimer = null;
  let rumorRouteFingerprint = '';
"""
rep(
    state_anchor,
    state_anchor + """  let rumorHunterState = null;
  let rumorHunterClanId = '';
  let rumorHunterNickname = '';
  let rumorHunterUnlockedCityIds = [];
  let rumorHunterCityCatalog = [];
  let rumorHunterReady = false;
  let rumorHunterRunning = false;
  let rumorHunterLease = null;
  let rumorHunterCurrent = null;
  let rumorHunterHeartbeatTimer = null;
  let rumorHunterRefreshTimer = null;
  let rumorHunterPushPromise = null;
""",
    "rumor hunter state"
)

insert_anchor = "  function renderRumorsTodaySummary() {"
need(insert_anchor, "rumor summary anchor")

module = r'''
  // Kokkaras private coordinator is NOT used. Game bearer tokens never leave HK.
  // Planner below mirrors Kokkaras 5.3.22-ui-icons-pit-dim Rumors Hunter v40.
  const RUMOR_HUNTER_EXPECTED_SIGNATURES={
    'aa3d99b6-054c-4add-a825-437eea6514be':'1bd0a1cfd8587aeb',
    'cac5d303-8251-4c5c-b5b1-0a3cb7789863':'fad3f6aed6663dab',
    'beb0a9a3-f4bd-4213-8285-429e9f0f064e':'f1538231ca63afd7',
    '165263b1-411c-4ce4-80b9-fbf5068d5b7c':'043e45add5a6ce4b',
    'caa3ccf0-cecd-4376-93f8-d11780859431':'7aadcce443549257',
    '0b07d8ca-3ad1-4e9f-80b7-fb59aeda5544':'2c0568f5c440af8e',
    '7b396fb3-2d66-4afd-85e4-98b9fd58a90a':'8662f7de16d6717e',
    'b5419fbd-f88b-4776-8106-ba7772be4370':'da9a75b19f32b9a4',
    '04d866e2-f582-4e4f-9faf-2722aec5cc17':'dbaf3642d6fd33f8',
    'bcb09d51-bad7-4ddf-a564-e6003ff9745f':'39c6cf2e6cf99348',
    '055abb57-8d7d-417c-b9f1-94766fc0eb44':'43c1d8d85fbf3709',
    '8184938e-f2e6-453c-9e0d-a16d87cbe46c':'e4219a17b927261e',
    '676c067f-ba9f-4f92-a150-9fd50dc2948d':'f8689a69800d7503',
    '3848bf1f-ba0e-4def-b4e1-7cd30f79406e':'c5048d85e82357a1',
    'a4a86f1e-70c4-43fa-b804-2a358dc6ae87':'299db1536a2529bf',
    'a98d8ea6-aac2-49ef-8c8c-8b50471a6c84':'2a02637b8b10eb32',
    '2cf24eee-6245-4692-bea5-daf949c063dc':'b0d316a1f4db0d59'
  };
  const RUMOR_HUNTER_POLICIES={
    'aa3d99b6-054c-4add-a825-437eea6514be':{kind:'moscow',threshold:.10},
    'cac5d303-8251-4c5c-b5b1-0a3cb7789863':{kind:'adaptive',threshold:.10},
    'beb0a9a3-f4bd-4213-8285-429e9f0f064e':{kind:'adaptive',threshold:.12},
    '165263b1-411c-4ce4-80b9-fbf5068d5b7c':{kind:'final',threshold:.06},
    'caa3ccf0-cecd-4376-93f8-d11780859431':{kind:'final',threshold:.03,gate:900},
    '0b07d8ca-3ad1-4e9f-80b7-fb59aeda5544':{kind:'paris',threshold:.08},
    '7b396fb3-2d66-4afd-85e4-98b9fd58a90a':{kind:'adaptive',threshold:.05},
    'b5419fbd-f88b-4776-8106-ba7772be4370':{kind:'adaptive',threshold:.09},
    '04d866e2-f582-4e4f-9faf-2722aec5cc17':{kind:'adaptive',threshold:.14},
    'bcb09d51-bad7-4ddf-a564-e6003ff9745f':{kind:'ny',threshold:.08,gate:800},
    '055abb57-8d7d-417c-b9f1-94766fc0eb44':{kind:'la',threshold:.04,gate:950},
    '8184938e-f2e6-453c-9e0d-a16d87cbe46c':{kind:'gated',threshold:.12,gate:300},
    '676c067f-ba9f-4f92-a150-9fd50dc2948d':{kind:'gated',threshold:.05,gate:550},
    '3848bf1f-ba0e-4def-b4e1-7cd30f79406e':{kind:'gated',threshold:.05,gate:280},
    'a4a86f1e-70c4-43fa-b804-2a358dc6ae87':{kind:'adaptive',threshold:.08},
    'a98d8ea6-aac2-49ef-8c8c-8b50471a6c84':{kind:'adaptive',threshold:.08},
    '2cf24eee-6245-4692-bea5-daf949c063dc':{kind:'adaptive',threshold:.08}
  };

  const rumorHunterCoordKey=(x,y)=>String(x)+','+String(y);
  const rumorHunterParseKey=value=>String(value).split(',').map(Number);
  const rumorHunterCheb=(a,b)=>Math.max(Math.abs(a[0]-b[0]),Math.abs(a[1]-b[1]));
  const rumorHunterSetDiff=(a,b)=>new Set([...a].filter(value=>!b.has(value)));
  const rumorHunterSetInter=(a,b)=>new Set([...a].filter(value=>b.has(value)));
  const rumorHunterSetUnion=(a,b)=>new Set([...a,...b]);
  const rumorHunterLexGt=(a,b)=>{
    if(b==null)return true;
    const n=Math.max(a.length,b.length);
    for(let i=0;i<n;i++){const A=a[i]??0,B=b[i]??0;if(A>B)return true;if(A<B)return false;}
    return false;
  };

  async function rumorHunterSha16(text) {
    try{
      const bytes=new TextEncoder().encode(String(text||''));
      const digest=await crypto.subtle.digest('SHA-256',bytes);
      return [...new Uint8Array(digest)].map(value=>value.toString(16).padStart(2,'0')).join('').slice(0,16);
    }catch(_){
      let hash=2166136261;
      for(const char of String(text||'')){hash^=char.charCodeAt(0);hash=Math.imul(hash,16777619);}
      return 'fnv-'+(hash>>>0).toString(16).padStart(8,'0');
    }
  }

  function rumorHunterType(rumorId) {
    const value=String(rumorId||'').toLowerCase();
    if(value.includes('jackpot'))return 'JACKPOT';
    if(value.includes('normal'))return 'NORMAL';
    if(value.includes('trash'))return 'TRASH';
    return 'UNKNOWN';
  }

  function rumorHunterAccountResearch() {
    const result=new Map();
    const rows=Array.isArray(playerDocument?.rumors?.researched_cells)?playerDocument.rumors.researched_cells:[];
    for(const row of rows){
      const gid=String(row?.gamearea_id||'').trim(),rid=String(row?.rumor_id||'').trim();
      if(gid&&rid)result.set(gid,rid);
    }
    return result;
  }

  async function rumorHunterSleep(ms) {
    let remain=Math.max(0,Number(ms)||0);
    while(remain>0){
      if(hkRunner.signal?.aborted)throw new DOMException('Aborted','AbortError');
      await hkRunner.waitIfPaused();
      const part=Math.min(500,remain);
      await sleep(part);
      remain-=part;
    }
  }

  class HKRumorCityHunter {
    constructor({city,areas,existingByGid}){
      this.city=city||{};
      this.cityId=String(this.city.id||'');
      this.label=String(this.city.name||this.city.city||this.cityId);
      this.coordToGid=new Map();this.gidToCoord=new Map();this.allCoords=new Set();this.primary=new Set();this.secondary=new Set();this.searchable=new Set();
      this.observations=new Map();this.invalid406=new Set();this.probeReasons=new Map();this.failedHotSeeds=new Set();this.neighbors=new Map();
      this.probes=0;this.posts=0;this.wait409=0;this.fallbackEnabled=false;this.cancelled=false;this.signature='';this.abortReason='';
      for(const area of (areas||[])){
        const info=area?.info||{},meta=area?.meta||{};
        const gid=String(info.gamearea_id||area?.id||area?.gamearea_id||'').trim();
        const x=Number(info.x??area?.x??area?.meta?.gamearea_coords?.x),y=Number(info.y??area?.y??area?.meta?.gamearea_coords?.y);
        if(!gid||!Number.isFinite(x)||!Number.isFinite(y))continue;
        const key=rumorHunterCoordKey(x,y);
        this.coordToGid.set(key,gid);this.gidToCoord.set(gid,key);this.allCoords.add(key);
        if(Number(info.tier??area?.tier)===2)this.primary.add(key);
        else{
          const values=[info.building_count,meta.buildings_total,meta.events_total,area?.building_count];
          if(values.some(value=>Number.isFinite(Number(value))&&Number(value)>0))this.secondary.add(key);
        }
      }
      this.searchable=new Set(this.primary);
      for(const key of this.allCoords){
        const [x,y]=rumorHunterParseKey(key),neighbors=[];
        for(let dx=-RUMOR_HUNTER_RADIUS;dx<=RUMOR_HUNTER_RADIUS;dx++)for(let dy=-RUMOR_HUNTER_RADIUS;dy<=RUMOR_HUNTER_RADIUS;dy++){
          const q=rumorHunterCoordKey(x+dx,y+dy);if(this.allCoords.has(q))neighbors.push(q);
        }
        this.neighbors.set(key,neighbors);
      }
      for(const [gid,rid] of (existingByGid||new Map()).entries()){
        const key=this.gidToCoord.get(String(gid));if(!key)continue;
        this.observations.set(key,[rumorHunterType(rid),String(rid||'')]);this.searchable.add(key);this.primary.add(key);
      }
    }
    display(key){const [x,y]=rumorHunterParseKey(key);return String(y).padStart(2,'0')+':'+String(x).padStart(2,'0');}
    log(message,type=''){log('[Слухи] '+this.label+' · '+String(message||''),type);}
    jackpots(){return new Set([...this.observations].filter(([,value])=>value[0]==='JACKPOT').map(([key])=>key));}
    nearSet(center,universe){const [x,y]=rumorHunterParseKey(center),out=new Set();for(let dx=-RUMOR_HUNTER_RADIUS;dx<=RUMOR_HUNTER_RADIUS;dx++)for(let dy=-RUMOR_HUNTER_RADIUS;dy<=RUMOR_HUNTER_RADIUS;dy++){const q=rumorHunterCoordKey(x+dx,y+dy);if(universe.has(q))out.add(q);}return out;}
    candidateSet(){
      let base=new Set(this.searchable);
      for(const key of this.invalid406)base.delete(key);
      for(const key of this.observations.keys())base.delete(key);
      const universe=rumorHunterSetUnion(base,this.searchable);
      for(const [key,value] of this.observations)if(value[0]==='TRASH')for(const q of this.nearSet(key,universe))base.delete(q);
      const found=this.jackpots(),remaining=RUMOR_HUNTER_JACKPOTS-found.size;
      if(remaining===1){
        for(const [key,value] of this.observations){
          if(value[0]!=='NORMAL')continue;
          if([...found].some(j=>rumorHunterCheb(rumorHunterParseKey(key),rumorHunterParseKey(j))<=RUMOR_HUNTER_RADIUS))continue;
          base=rumorHunterSetInter(base,this.nearSet(key,rumorHunterSetUnion(base,this.searchable)));
        }
      }
      return base;
    }
    contaminated(key){const point=rumorHunterParseKey(key);return [...this.jackpots()].some(j=>rumorHunterCheb(point,rumorHunterParseKey(j))<=RUMOR_HUNTER_RADIUS);}
    normalSupport(key){
      const found=this.jackpots(),point=rumorHunterParseKey(key);let score=0;
      for(const [q,value] of this.observations){
        if(value[0]!=='NORMAL')continue;
        const a=rumorHunterParseKey(q);
        if([...found].some(j=>rumorHunterCheb(a,rumorHunterParseKey(j))<=RUMOR_HUNTER_RADIUS))continue;
        if(rumorHunterCheb(a,point)<=RUMOR_HUNTER_RADIUS)score++;
      }
      return score;
    }
    guaranteedHotNormals(){
      const found=this.jackpots(),candidates=this.candidateSet(),rows=[];
      for(const [key,value] of this.observations){
        if(value[0]!=='NORMAL')continue;
        const point=rumorHunterParseKey(key);
        if([...found].some(j=>rumorHunterCheb(point,rumorHunterParseKey(j))<=RUMOR_HUNTER_RADIUS))continue;
        if(this.failedHotSeeds.has(key+'|'+found.size))continue;
        const near=this.nearSet(key,candidates);if(near.size)rows.push([key,near.size]);
      }
      rows.sort((a,b)=>a[1]-b[1]||a[0].localeCompare(b[0]));
      return rows.map(row=>row[0]);
    }
    previousGlobal(){
      const accepted=new Set(['global_exact_marginal','direct_ordinary','close_fallback_boundary','paris_final_tie_close']);
      return [...this.probeReasons].filter(([,reason])=>accepted.has(reason)).map(([key])=>key);
    }
    chooseGlobal(candidates){
      const probes=[...this.searchable].filter(key=>!this.observations.has(key)&&!this.invalid406.has(key)&&!this.contaminated(key));
      if(!probes.length||!candidates.size)return null;
      const previous=this.previousGlobal();let rows=[],maxGain=0;
      for(const p of probes){
        let gain=0;for(const q of (this.neighbors.get(p)||[]))if(candidates.has(q))gain++;
        if(gain<=0)continue;
        const pp=rumorHunterParseKey(p);let spread=999;
        if(previous.length)spread=Math.min(...previous.map(q=>rumorHunterCheb(pp,rumorHunterParseKey(q))));
        const self=candidates.has(p)?1:0,staticSize=(this.neighbors.get(p)||[]).reduce((n,q)=>n+(this.primary.has(q)?1:0),0);
        rows.push({p,gain,spread,self,staticSize});maxGain=Math.max(maxGain,gain);
      }
      if(!rows.length)return null;
      let tied=rows.filter(row=>row.gain===maxGain);
      let bestValue=Math.max(...tied.map(row=>row.spread));tied=tied.filter(row=>row.spread===bestValue);
      bestValue=Math.max(...tied.map(row=>row.self));tied=tied.filter(row=>row.self===bestValue);
      let best=tied[0]?.p||null,bestKey=null;
      for(const row of tied){
        const covered=new Set((this.neighbors.get(row.p)||[]).filter(q=>candidates.has(q)));let residual=0;
        for(const q of probes){
          if(q===row.p)continue;let gain=0;
          for(const z of (this.neighbors.get(q)||[]))if(candidates.has(z)&&!covered.has(z))gain++;
          residual=Math.max(residual,gain);
        }
        const [x,y]=rumorHunterParseKey(row.p),score=[residual,row.staticSize,-y,-x];
        if(rumorHunterLexGt(score,bestKey)){bestKey=score;best=row.p;}
      }
      return best;
    }
    chooseCloseFallback(candidates){
      const probes=[...this.searchable].filter(key=>!this.observations.has(key)&&!this.invalid406.has(key)&&!this.contaminated(key));
      let best=null,bestScore=null;
      for(const p of probes){
        let covered=0;for(const q of (this.neighbors.get(p)||[]))if(candidates.has(q))covered++;
        if(covered<=0)continue;
        const [x,y]=rumorHunterParseKey(p),score=[covered,candidates.has(p)?1:0,-y,-x];
        if(rumorHunterLexGt(score,bestScore)){bestScore=score;best=p;}
      }
      return best;
    }
    chooseSplit(cluster,globalCandidates,minimax=false){
      if(!cluster.size)return null;
      const coords=[...cluster].map(rumorHunterParseKey);
      const minx=Math.min(...coords.map(c=>c[0]))-RUMOR_HUNTER_RADIUS,maxx=Math.max(...coords.map(c=>c[0]))+RUMOR_HUNTER_RADIUS;
      const miny=Math.min(...coords.map(c=>c[1]))-RUMOR_HUNTER_RADIUS,maxy=Math.max(...coords.map(c=>c[1]))+RUMOR_HUNTER_RADIUS;
      const probes=[...this.searchable].filter(key=>{
        if(this.observations.has(key)||this.invalid406.has(key)||this.contaminated(key))return false;
        const [x,y]=rumorHunterParseKey(key);return x>=minx&&x<=maxx&&y>=miny&&y<=maxy;
      });
      const n=cluster.size;let best=null,bestScore=null;
      for(const p of probes){
        const nhood=this.nearSet(p,globalCandidates),insideSet=rumorHunterSetInter(cluster,nhood),inside=insideSet.size;
        if(inside<=0)continue;
        const jackpot=cluster.has(p)?1:0,normal=inside-jackpot,trash=n-inside;
        if(jackpot===0&&(normal===0||trash===0))continue;
        const expected=normal*normal+trash*trash,worst=Math.max(normal,trash),outside=rumorHunterSetDiff(nhood,cluster).size,clean=outside===0?1:0,support=this.normalSupport(p);
        const [x,y]=rumorHunterParseKey(p),score=minimax?[-worst,-expected,-outside,clean,jackpot,support,-y,-x]:[-expected,-worst,-outside,clean,jackpot,support,-y,-x];
        if(rumorHunterLexGt(score,bestScore)){bestScore=score;best=p;}
      }
      return best;
    }
    async localize(seed,minimax=false){
      let global=this.candidateSet(),cluster=this.nearSet(seed,global);if(!cluster.size)return false;
      const start=this.jackpots().size;
      for(let step=0;step<28;step++){
        if(this.cancelled||hkRunner.signal?.aborted)return false;
        await hkRunner.waitIfPaused();
        if(this.jackpots().size>start)return true;
        global=this.candidateSet();cluster=rumorHunterSetInter(cluster,global);if(!cluster.size)return false;
        if(cluster.size===1){const p=[...cluster][0],result=await this.doSearch(p,'local_exact');return result.type==='JACKPOT';}
        let p=this.chooseSplit(cluster,global,minimax),reason='local_info';
        if(!p){
          let best=null,bestScore=null;
          for(const q of cluster){const [x,y]=rumorHunterParseKey(q),score=[this.normalSupport(q),this.nearSet(q,cluster).size,-y,-x];if(rumorHunterLexGt(score,bestScore)){bestScore=score;best=q;}}
          p=best;reason='local_direct_fallback';
        }
        const before=new Set(global),nhood=this.nearSet(p,before),outside=rumorHunterSetDiff(nhood,cluster).size,result=await this.doSearch(p,reason),type=result.type;
        if(type==='JACKPOT')return true;
        if(type==='TRASH')cluster=rumorHunterSetDiff(cluster,nhood);
        else if(type==='NORMAL'){
          if(outside===0){cluster=rumorHunterSetInter(cluster,nhood);cluster.delete(p);}
          else{const local=rumorHunterSetInter(cluster,nhood);if(local.size&&local.size<cluster.size){cluster=local;cluster.delete(p);}}
        }else if(type==='INVALID')cluster.delete(p);
        else if(type==='ERROR')return false;
      }
      return false;
    }
    closeProbability(closeCount,totalCount,remaining){
      if(closeCount<=0||totalCount<=0||remaining<=0)return 0;
      remaining=Math.min(remaining,totalCount);const ordinary=totalCount-closeCount;if(ordinary<remaining)return 1;
      let none=1;for(let k=0;k<remaining;k++)none*=((ordinary-k)/(totalCount-k));return 1-none;
    }
    enableFallback(){for(const q of this.secondary)if(!this.searchable.has(q)&&!this.invalid406.has(q))this.searchable.add(q);this.fallbackEnabled=true;}
    async geometrySignature(){
      const coords=[...this.primary].map(rumorHunterParseKey).sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
      return rumorHunterSha16(coords.map(c=>String(c[0])+','+String(c[1])).join(';'));
    }
    jackpotPoints(){
      const rows=[];
      for(const key of this.jackpots()){
        const gid=this.coordToGid.get(key),rid=this.observations.get(key)?.[1]||'rumor_jackpot_hunter';
        const [gridX,gridY]=rumorHunterParseKey(key);
        if(gid)rows.push({x:gridY,y:gridX,gamearea_id:gid,rumor_id:String(rid||'rumor_jackpot_hunter')});
      }
      return rows.slice(0,3);
    }
    async run(){
      this.signature=await this.geometrySignature();
      const expected=RUMOR_HUNTER_EXPECTED_SIGNATURES[this.cityId]||'';
      const guardOk=!expected||expected===this.signature;
      const policy=guardOk?(RUMOR_HUNTER_POLICIES[this.cityId]||{kind:'baseline'}):{kind:'baseline'};
      if(!guardOk)this.log(either('Сигнатура карты изменилась — безопасный базовый планировщик.','Map signature changed — safe baseline planner.'),'warn');
      while(this.jackpots().size<RUMOR_HUNTER_JACKPOTS){
        if(this.cancelled||hkRunner.signal?.aborted)break;
        await hkRunner.waitIfPaused();
        let candidates=this.candidateSet(),localized=false;
        for(const seed of this.guaranteedHotNormals()){
          const before=this.jackpots().size;
          if(await this.localize(seed,policy.kind==='ny')){localized=true;break;}
          this.failedHotSeeds.add(seed+'|'+before);
        }
        if(localized)continue;
        candidates=this.candidateSet();
        if(!candidates.size){if(!this.fallbackEnabled){this.enableFallback();continue;}break;}
        const found=this.jackpots(),remaining=RUMOR_HUNTER_JACKPOTS-found.size;
        const ordinary=new Set([...candidates].filter(c=>![...found].some(j=>rumorHunterCheb(rumorHunterParseKey(c),rumorHunterParseKey(j))<=RUMOR_HUNTER_RADIUS)));
        const close=rumorHunterSetDiff(candidates,ordinary),prob=this.closeProbability(close.size,candidates.size,remaining);
        let useClose=false,p=null,reason='';
        if(policy.kind==='paris'){
          const useTie=remaining===1&&ordinary.size>0&&close.size>0&&prob>=policy.threshold;
          if(ordinary.size){p=this.chooseGlobal(ordinary);reason=useTie?'paris_final_tie_close':'global_exact_marginal';}
          if(!p){p=this.chooseCloseFallback(candidates)||[...candidates][0]||null;reason='close_fallback_boundary';}
        }else{
          if(policy.kind==='moscow')useClose=found.size>=2&&close.size>0&&(close.size/candidates.size)>=policy.threshold;
          else if(policy.kind==='final')useClose=remaining===1&&close.size>0&&prob>=policy.threshold&&(policy.gate==null||candidates.size<=policy.gate);
          else if(policy.kind==='ny')useClose=remaining===1&&close.size>0&&candidates.size<=policy.gate&&prob>=policy.threshold;
          else if(policy.kind==='gated'||policy.kind==='la')useClose=found.size>0&&close.size>0&&candidates.size<=policy.gate&&prob>=policy.threshold;
          else if(policy.kind==='adaptive')useClose=found.size>0&&close.size>0&&prob>=policy.threshold;
          if(useClose){p=this.chooseGlobal(candidates)||this.chooseCloseFallback(candidates)||[...candidates][0]||null;reason='global_exact_marginal';}
          else if(ordinary.size){p=this.chooseGlobal(ordinary)||[...ordinary][0]||null;reason='direct_ordinary';}
          else{p=this.chooseCloseFallback(candidates)||[...candidates][0]||null;reason='close_fallback_boundary';}
        }
        if(!p)break;
        const result=await this.doSearch(p,reason);
        if(result.type==='NORMAL')await this.localize(p,policy.kind==='ny');
        else if(result.type==='ERROR')break;
      }
      return this.jackpotPoints();
    }
  }

  async function rumorHunterCall(action,extra={}) {
    if(!rumorHunterClanId)throw new Error(either('Не определён ID клана','Clan ID is unavailable'));
    return rumorServerJson('/hunter',{
      action:String(action||'state'),
      clan_id:rumorHunterClanId,
      nickname:rumorHunterNickname,
      timezone:Intl.DateTimeFormat().resolvedOptions().timeZone||'',
      unlocked_city_ids:rumorHunterUnlockedCityIds,
      ...extra
    },false);
  }

  function rumorHunterApplyState(value) {
    const state=value?.state&&typeof value.state==='object'?value.state:value;
    if(state&&typeof state==='object'&&Array.isArray(state.cities))rumorHunterState=state;
    renderRumorsPage();
    return rumorHunterState;
  }

  async function rumorHunterPrepareContext(force=false) {
    if(!force&&rumorHunterClanId&&rumorHunterUnlockedCityIds.length&&rumorHunterCityCatalog.length)return true;
    playerDocument=await hkAuthoritativePlayerRead('rumors-hunter:context');
    let clanDocument={};
    try{clanDocument=await apiJson('/clan/info','GET',null,true,1);}catch(_){}
    rumorHunterClanId=clean(clanIdentity({}, {}, clanDocument));
    if(!rumorHunterClanId)throw new Error(either('Не удалось определить клан аккаунта','Could not determine the account clan'));
    rumorHunterNickname=clean(playerDocument?.player?.nickname||playerDocument?.player?.name||playerDocument?.player?.username||playerIdentity(playerDocument?.player||{}));
    const citiesValue=await apiJson('/cities','GET',null,true,1);
    rumorHunterCityCatalog=Array.isArray(citiesValue)?citiesValue:(Array.isArray(citiesValue?.cities)?citiesValue.cities:[]);
    const allowed=new Set(Object.keys(RUMOR_HUNTER_EXPECTED_SIGNATURES));
    const unlocked=new Set();
    for(const area of (playerDocument?.areas?.areas||[])){
      const cityId=String(area?.city_id||area?.cityId||'').trim();
      if(allowed.has(cityId))unlocked.add(cityId);
    }
    for(const city of rumorHunterCityCatalog){
      const cityId=String(city?.id||'').trim();
      if(!allowed.has(cityId))continue;
      if(city?.unlocked===true||city?.opened===true||city?.is_open===true||city?.available===true)unlocked.add(cityId);
    }
    rumorHunterUnlockedCityIds=[...unlocked];
    if(!rumorHunterUnlockedCityIds.length)throw new Error(either('Не удалось определить открытые города аккаунта','Could not determine unlocked account cities'));
    return true;
  }

  async function refreshRumorHunterState(loud=false) {
    try{
      await rumorHunterPrepareContext(false);
      const result=await rumorHunterCall('state');
      rumorHunterApplyState(result);
      scheduleRumorHunterRefresh();
      return rumorHunterState;
    }catch(error){
      if(loud)log(either('Ошибка координатора слухов','Rumor coordinator error')+': '+(error?.message||error),'warn');
      return rumorHunterState;
    }
  }

  function scheduleRumorHunterRefresh() {
    if(rumorHunterRefreshTimer)return;
    rumorHunterRefreshTimer=setTimeout(async()=>{
      rumorHunterRefreshTimer=null;
      try{
        const page=root?.querySelector?.('[data-content="rumors"]');
        if(page?.classList?.contains('active')&&!rumorHunterRunning)await refreshRumorHunterState(false);
      }finally{scheduleRumorHunterRefresh();}
    },15000);
  }

  async function rumorHunterPushProgress(hunter) {
    if(!hunter||!rumorHunterLease||String(rumorHunterLease.city_id)!==String(hunter.cityId))return true;
    if(rumorHunterPushPromise)return rumorHunterPushPromise;
    rumorHunterPushPromise=(async()=>{
      try{
        const result=await rumorHunterCall('progress',{
          city_id:hunter.cityId,
          lease_token:String(rumorHunterLease.lease_token||''),
          probes:hunter.probes,
          posts:hunter.posts,
          wait409:hunter.wait409,
          jackpots:hunter.jackpotPoints()
        });
        rumorHunterApplyState(result);
        if(result?.ok===false){
          hunter.abortReason=String(result.error||'LEASE_LOST');
          return false;
        }
        return true;
      }catch(error){
        recordDiagnostic('rumors-hunter-progress-error',{city_id:hunter.cityId,message:String(error?.message||error).slice(0,500)});
        return true;
      }finally{rumorHunterPushPromise=null;}
    })();
    return rumorHunterPushPromise;
  }

  async function rumorHunterHeartbeat() {
    if(!rumorHunterReady)return;
    try{
      if(rumorHunterCurrent&&rumorHunterLease)await rumorHunterPushProgress(rumorHunterCurrent);
      const result=await rumorHunterCall('heartbeat',{ready:true});
      rumorHunterApplyState(result);
    }catch(error){
      recordDiagnostic('rumors-hunter-heartbeat-error',{message:String(error?.message||error).slice(0,500)});
    }
  }

  function scheduleRumorHunterHeartbeat() {
    if(rumorHunterHeartbeatTimer)return;
    rumorHunterHeartbeatTimer=setTimeout(async()=>{
      rumorHunterHeartbeatTimer=null;
      try{await rumorHunterHeartbeat();}finally{if(rumorHunterReady)scheduleRumorHunterHeartbeat();}
    },20000);
  }

  async function rumorHunterRelease(action='release') {
    if(!rumorHunterLease)return;
    try{
      const result=await rumorHunterCall(action,{
        city_id:String(rumorHunterLease.city_id||''),
        lease_token:String(rumorHunterLease.lease_token||'')
      });
      rumorHunterApplyState(result);
    }catch(_){}
    rumorHunterLease=null;
  }

  async function rumorHunterLeave() {
    rumorHunterReady=false;
    if(rumorHunterCurrent)rumorHunterCurrent.cancelled=true;
    try{
      if(rumorHunterClanId){
        const result=await rumorHunterCall('leave');
        rumorHunterApplyState(result);
      }
    }catch(_){}
    rumorHunterLease=null;rumorHunterCurrent=null;
  }

  async function rumorHunterLoadCityAreas(cityId) {
    const value=await apiJson('/city/'+encodeURIComponent(cityId)+'/game_area','GET',null,true,1);
    return Array.isArray(value)?value:(Array.isArray(value?.areas)?value.areas:[]);
  }

  function rumorHunterCityLabel(city) {
    const key=String(city?.city_key||'').trim();
    const translated=key?gameText(key):'';
    return String(translated&&translated!==key?translated:(city?.name||city?.city||key||either('Город','City')));
  }

  HKRumorCityHunter.prototype.doSearch=async function(key,reason){
    if(this.cancelled||hkRunner.signal?.aborted)return {coord:key,type:'ERROR',source:'cancelled'};
    if(this.observations.has(key)){const [type,rid]=this.observations.get(key);return {coord:key,type,rumor_id:rid,source:'existing'};}
    if(this.invalid406.has(key))return {coord:key,type:'INVALID',source:'known_406'};
    const gid=this.coordToGid.get(key);if(!gid)return {coord:key,type:'INVALID',source:'no_gid'};
    this.probes++;this.probeReasons.set(key,reason);
    while(true){
      if(this.cancelled||hkRunner.signal?.aborted)return {coord:key,type:'ERROR',source:'cancelled'};
      await hkRunner.waitIfPaused();
      try{
        const response=await apiJson('/rumors/search','POST',{gamearea_id:gid},true,0,18000);
        this.posts++;
        let rid=rumorJackpotIdFromResponse(response,gid);
        if(!rid){
          const researched=Array.isArray(response?.rumors?.researched_cells)?response.rumors.researched_cells:[];
          for(let i=researched.length-1;i>=0;i--)if(String(researched[i]?.gamearea_id||'')===gid){rid=String(researched[i]?.rumor_id||'');break;}
        }
        if(!rid)rid=String(response?.rumor_id||response?.id||'');
        const type=rumorHunterType(rid);
        this.observations.set(key,[type,rid]);
        this.log('['+String(this.probes).padStart(2,'0')+'] '+this.display(key)+' — '+type,type==='JACKPOT'?'ok':type==='TRASH'?'warn':'');
        await rumorHunterPushProgress(this);
        return {coord:key,type,rumor_id:rid,source:'new'};
      }catch(error){
        const status=Number(error?.httpStatus||0);
        const raw=String(error?.apiData?.message||error?.apiData?.description||error?.message||error||'');
        const low=raw.toLowerCase();
        if(status===429){
          const delay=Math.max(3000,Number(error?.retryAfterMs||20000));
          this.log(either('429 — жду cooldown','429 — waiting for cooldown'),'warn');
          await rumorHunterSleep(delay);continue;
        }
        if(status===409&&low.includes('new rumors are not')&&(low.includes('available')||low.includes('avaliable'))){
          this.wait409++;
          if(this.wait409===1)this.log(either('Слухи ещё не открыты — повторяю ту же клетку','Rumors are not open yet — retrying the same cell'),'warn');
          await rumorHunterPushProgress(this);
          await rumorHunterSleep(5000);continue;
        }
        if(status===409&&(low.includes('already searched rumor')||low.includes('already')&&low.includes('rumor'))){
          this.posts++;
          try{playerDocument=await hkAuthoritativePlayerRead('rumors-hunter:recover-409');}catch(_){}
          const rid=rumorHunterAccountResearch().get(gid)||'';
          if(rid){
            const type=rumorHunterType(rid);this.observations.set(key,[type,rid]);
            this.log(this.display(key)+' — '+type+' · 409 recovered','warn');
            await rumorHunterPushProgress(this);
            return {coord:key,type,rumor_id:rid,source:'recovered'};
          }
          this.abortReason='block_release';this.log(this.display(key)+' — 409 unresolved','bad');
          return {coord:key,type:'ERROR',source:'409-unresolved'};
        }
        if(status===406&&low.includes('no rumor')){
          this.posts++;this.invalid406.add(key);this.searchable.delete(key);
          this.log(this.display(key)+' — 406','warn');await rumorHunterPushProgress(this);
          return {coord:key,type:'INVALID',source:'406'};
        }
        if(/does.{0,20}not.{0,20}have.{0,20}city|нет.{0,30}город/i.test(raw))this.abortReason='city-unavailable';
        else this.abortReason='release';
        this.log(this.display(key)+' — '+raw,'bad');
        return {coord:key,type:'ERROR',source:'error'};
      }
    }
  };

  async function runRumorHunter() {
    if(!requireLicense()||rumorHunterRunning)return;
    if(hkRunner.running){alert(either('Сначала завершите текущую задачу','Finish the current task first'));return;}
    rumorHunterRunning=true;
    let completedNormally=false;
    try{
      await rumorHunterPrepareContext(true);
      rumorHunterReady=true;
      let stateResult=await rumorHunterCall('heartbeat',{ready:true});
      let state=rumorHunterApplyState(stateResult);
      scheduleRumorHunterHeartbeat();
      hkRunner.start({title:either('Охота за слухами','Rumors Hunter'),total:Number(state?.total||17),step:either('Распределение городов','Assigning cities'),pausable:true,stoppable:true});
      while(true){
        if(hkRunner.signal?.aborted)throw new DOMException('Aborted','AbortError');
        await hkRunner.waitIfPaused();
        stateResult=await rumorHunterCall('heartbeat',{ready:true});
        state=rumorHunterApplyState(stateResult);
        const total=Number(state?.total||17),done=Number(state?.complete||0);
        hkRunner.setStep(either('Готово городов ','Cities done ')+done+'/'+total,done,total);
        if(done>=total){completedNormally=true;break;}
        const selfId=String(state?.self_player_id||'');
        const mine=new Set((state?.self_search_city_ids||[]).map(String));
        const city=(state?.cities||[]).find(row=>mine.has(String(row?.city_id||''))&&String(row?.assigned_player_id||'')===selfId&&row?.status!=='done');
        if(!city){
          hkRunner.note(either('Жду назначение города','Waiting for a city assignment'),'info');
          await rumorHunterSleep(3000);continue;
        }
        hkRunner.setStep(either('Получаю город: ','Claiming city: ')+rumorHunterCityLabel(city),done,total);
        const claim=await rumorHunterCall('claim',{city_id:String(city.city_id)});
        state=rumorHunterApplyState(claim);
        if(!claim?.ok){
          if(claim?.error==='RESULT_READY'){await refreshRumorRouteQuietly();continue;}
          await rumorHunterSleep(1500);continue;
        }
        rumorHunterLease={city_id:String(city.city_id),lease_token:String(claim.lease_token||''),lease_until:Number(claim.lease_until||0)};
        const areas=await rumorHunterLoadCityAreas(city.city_id);
        if(!areas.length){
          log(either('Сетка города не загружена: ','City grid unavailable: ')+rumorHunterCityLabel(city),'warn');
          await rumorHunterRelease('release');continue;
        }
        try{playerDocument=await hkAuthoritativePlayerRead('rumors-hunter:city-start');}catch(_){}
        const cityMeta=rumorHunterCityCatalog.find(row=>String(row?.id||'')===String(city.city_id))||{};
        const hunter=new HKRumorCityHunter({
          city:{id:String(city.city_id),name:rumorHunterCityLabel(city)||cityLabel(cityMeta)},
          areas,
          existingByGid:rumorHunterAccountResearch()
        });
        rumorHunterCurrent=hunter;
        hkRunner.setStep(rumorHunterCityLabel(city)+' · '+either('поиск 0/3','search 0/3'),done,total);
        const points=await hunter.run();
        if(hkRunner.signal?.aborted)throw new DOMException('Aborted','AbortError');
        if(points.length>=3){
          const result=await rumorHunterCall('done',{
            city_id:String(city.city_id),
            lease_token:String(rumorHunterLease?.lease_token||''),
            jackpots:points,
            probes:hunter.probes,
            posts:hunter.posts,
            wait409:hunter.wait409
          });
          rumorHunterApplyState(result);
          if(result?.ok){
            log('★ '+rumorHunterCityLabel(city)+' — 3/3','ok');
            await refreshRumorRouteQuietly();
          }else if(result?.error!=='RESULT_READY'){
            await rumorHunterRelease('release');
          }
        }else if(hunter.abortReason==='RESULT_READY'){
          await refreshRumorHunterState(false);
        }else{
          await rumorHunterRelease(hunter.abortReason==='block_release'?'block_release':'release');
        }
        rumorHunterCurrent=null;rumorHunterLease=null;
      }
      hkRunner.finish(either('Охота за слухами завершена','Rumors Hunter completed'));
      await refreshRumorRouteQuietly();
    }catch(error){
      if(error?.name==='AbortError'){
        hkRunner.reset();log(either('Охота за слухами остановлена','Rumors Hunter stopped'),'warn');
      }else{
        hkRunner.fail(error);log(either('Ошибка охоты за слухами','Rumors Hunter error')+': '+(error?.message||error),'bad');
      }
    }finally{
      if(rumorHunterCurrent)rumorHunterCurrent.cancelled=true;
      await rumorHunterLeave();
      rumorHunterRunning=false;
      if(!completedNormally&&hkRunner.state.status==='done')hkRunner.reset();
      renderRumorsPage();
    }
  }

  function rumorHunterStatusLabel(city) {
    if(city?.status==='done')return either('ГОТОВО','DONE');
    if(city?.status==='running')return either('ПОИСК','SEARCHING');
    if(city?.status==='queued')return either('В ОЧЕРЕДИ','QUEUED');
    return either('НЕ НАЗНАЧЕН','UNASSIGNED');
  }

  function rumorHunterAgeLabel(timestamp) {
    const value=Number(timestamp||0);if(!value)return '—';
    const seconds=Math.max(0,Math.floor(Date.now()/1000-value));
    if(seconds<60)return seconds+either(' сек.',' sec.');
    if(seconds<3600)return Math.floor(seconds/60)+either(' мин.',' min.');
    return Math.floor(seconds/3600)+either(' ч.',' h.');
  }

'''
s=s.replace(insert_anchor,module+insert_anchor,1)

summary_start="  function renderRumorsTodaySummary() {"
summary_end="\n  function renderRumorsPage() {"
need(summary_start,"summary start"); need(summary_end,"summary end")
a=s.index(summary_start); b=s.index(summary_end,a)
summary=r'''  function renderRumorsTodaySummary() {
    scheduleRumorAutoRefresh();
    const host=root?.querySelector?.('#hk-rumors-today-summary');
    if(!host)return;
    const complete=dailyRumorRoute.filter(route=>rumorRouteProgress(route)>=3).length;
    const total=dailyRumorRoute.length;
    const points=dailyRumorRoute.reduce((sum,row)=>sum+(row?.points?.length||0),0);
    const routePreview=total?dailyRumorRoute.map(route=>{
      const rows=(route?.points||[]).map(point=>{
        const coord=String(Number(point?.x))+':'+String(Number(point?.y)).padStart(2,'0');
        const area=rumorRoutePointIds(point)[0]||'';
        return '<button type="button" class="hk-rumor-summary-point" data-rumor-area="'+escapeHtml(area)+'"><b>★ '+escapeHtml(coord)+'</b><small>'+either('Джекпот · карта','Jackpot · map')+'</small></button>';
      }).join('');
      return '<div class="hk-rumor-summary-city"><strong>'+escapeHtml(rumorRouteCityLabel(route))+'</strong><div>'+rows+'</div></div>';
    }).join(''):'<span class="hk-muted">'+either('Координаты ещё не опубликованы.','Coordinates are not published yet.')+'</span>';
    host.innerHTML=
      '<div class="hk-rumor-summary-head"><div><h3>'+either('Слухи сегодня','Rumors today')+'</h3><small>'+escapeHtml(rumorRouteSourceLabel())+' · '+escapeHtml(rumorRouteUpdatedLabel())+' · '+either('автообновление 30 сек.','auto refresh 30 sec.')+'</small></div><b>'+complete+'/'+(total||17)+'</b></div>'+
      '<div class="hk-rumor-summary-meta"><span>'+either('Городов','Cities')+': <b>'+(total||'—')+'</b></span><span>'+either('Точек','Points')+': <b>'+(points||'—')+'</b></span></div>'+
      '<details class="hk-rumor-summary-routes" open><summary>'+either('Актуальные джекпоты','Current jackpots')+'</summary><div>'+routePreview+'</div></details>'+
      '<div class="hk-rumor-summary-actions"><button type="button" id="hk-rumors-summary-open" class="hk-primary">'+either('Открыть охоту','Open hunter')+'</button><button type="button" id="hk-rumors-summary-refresh" class="hk-secondary">'+either('Обновить','Refresh')+'</button></div>';
    host.querySelector('#hk-rumors-summary-open')?.addEventListener('click',()=>runtime.navigate?.('rumors'));
    host.querySelector('#hk-rumors-summary-refresh')?.addEventListener('click',()=>void refreshRumorsPage());
    host.querySelectorAll('[data-rumor-area]').forEach(button=>button.addEventListener('click',()=>{
      const area=String(button.dataset.rumorArea||'');if(!area)return;
      runtime.navigate?.('maps');void openMapDetail(area,area);
    }));
  }
'''
s=s[:a]+summary+s[b:]

page_start="  function renderRumorsPage() {"
page_end="\n  async function refreshRumorsPage() {"
need(page_start,"page start"); need(page_end,"page end")
a=s.index(page_start); b=s.index(page_end,a)
page=r'''  function renderRumorsPage() {
    scheduleRumorAutoRefresh();
    scheduleRumorHunterRefresh();
    if(!rumorBox)return;
    const state=rumorHunterState;
    const players=new Map((state?.players||[]).map(row=>[String(row?.player_id||''),String(row?.nickname||'')]));
    const cities=Array.isArray(state?.cities)?state.cities:[];
    const complete=Number(state?.complete||dailyRumorRoute.filter(route=>rumorRouteProgress(route)>=3).length);
    const total=Number(state?.total||17);
    const activeTitle=String(hkRunner.state.title||'')===either('Охота за слухами','Rumors Hunter')&&hkRunner.running;
    const cards=cities.length?cities.map(city=>{
      const assignedId=String(city?.assigned_player_id||''),assigned=players.get(assignedId)||'';
      const points=(city?.jackpots||[]).map(point=>{
        const coord=String(Number(point?.x))+':'+String(Number(point?.y)).padStart(2,'0');
        const area=String(point?.gamearea_id||'');
        return '<button type="button" class="hk-rumor-point done" data-rumor-area="'+escapeHtml(area)+'"><b>★ '+escapeHtml(coord)+'</b><small>'+either('Джекпот · открыть','Jackpot · open')+'</small></button>';
      }).join('');
      const empty=points||'<span class="hk-muted">'+either('координаты ищутся','coordinates pending')+'</span>';
      return '<article class="hk-rumor-city '+(city?.status==='done'?'done':'')+'">'+
        '<div><b>'+escapeHtml(rumorHunterCityLabel(city))+'</b><span>'+escapeHtml(rumorHunterStatusLabel(city))+'</span></div>'+
        '<div class="hk-rumor-city-meta"><small>'+either('Назначен','Assigned')+': '+escapeHtml(assigned||'—')+'</small><small>'+either('проверок','probes')+': '+Number(city?.probes||0)+' · POST: '+Number(city?.posts||0)+' · 409: '+Number(city?.wait409||0)+'</small></div>'+
        '<div class="hk-rumor-points">'+empty+'</div></article>';
    }).join(''):'<p class="hk-muted">'+either('Подключаю координатор и загружаю 17 городов…','Connecting coordinator and loading 17 cities…')+'</p>';
    const readyCount=(state?.players||[]).filter(row=>row?.ready).length;
    const mine=(state?.self_search_city_ids||[]).length;
    const history=(state?.history||[]).slice(0,12).map(row=>{
      const city=cities.find(city=>String(city?.city_id||'')===String(row?.city_id||''));
      const who=players.get(String(row?.player_id||''))||either('игрок','player');
      const labels={claim:either('начал поиск','started search'),done:either('завершил 3/3','completed 3/3'),release:either('освободил город','released city'),block_release:either('освободил после конфликта','released after conflict'),leave:either('вышел из охоты','left hunter'),open:either('открыл слухи','opened rumors')};
      return '<div class="hk-rumor-history-row"><b>'+escapeHtml(who)+'</b><span>'+escapeHtml(labels[row?.event]||String(row?.event||''))+(city?' · '+escapeHtml(rumorHunterCityLabel(city)):'')+'</span><small>'+escapeHtml(rumorHunterAgeLabel(row?.created_at))+'</small></div>';
    }).join('');
    const pauseLabel=hkRunner.state.status==='paused'?either('Продолжить','Resume'):either('Пауза','Pause');
    rumorBox.innerHTML=
      '<div class="hk-rumor-hero"><div><h3>'+either('Охота за слухами','Rumors Hunter')+'</h3><p>'+either('Канон Kokkaras v40: один назначенный город ищет один охотник до 3/3; готовые результаты Kokkaras и HK сразу исключаются из повторного поиска.','Kokkaras v40 canon: one assigned city stays with one hunter until 3/3; ready Kokkaras and HK results are never searched twice.')+'</p></div><div class="hk-rumor-source"><b>'+escapeHtml(rumorRouteSourceLabel())+'</b><small>'+escapeHtml(rumorRouteUpdatedLabel())+'</small></div></div>'+
      '<div class="hk-rumor-stats"><span>'+either('Готово','Done')+' <b>'+complete+'/'+total+'</b></span><span>'+either('Готовых охотников','Ready hunters')+' <b>'+readyCount+'</b></span><span>'+either('Мне назначено','Assigned to me')+' <b>'+mine+'</b></span></div>'+
      '<div class="hk-rumor-actions"><button type="button" id="hk-rumors-start" class="hk-primary" '+(activeTitle?'disabled':'')+'>'+either('Начать охоту','Start hunting')+'</button><button type="button" id="hk-rumors-refresh" class="hk-secondary">'+either('Обновить','Refresh')+'</button><button type="button" id="hk-rumors-copy">'+either('Копировать слухи','Copy rumors')+'</button>'+(activeTitle?'<button type="button" id="hk-rumors-pause" class="hk-secondary">'+pauseLabel+'</button><button type="button" id="hk-rumors-stop" class="hk-danger">'+either('Стоп','Stop')+'</button>':'')+'</div>'+
      '<div class="hk-rumor-grid">'+cards+'</div>'+
      '<details class="hk-rumor-history" '+(history?'open':'')+'><summary>'+either('История / актуальность','History / freshness')+'</summary><div>'+(history||'<span class="hk-muted">'+either('Событий пока нет','No events yet')+'</span>')+'</div></details>';
    rumorBox.querySelector('#hk-rumors-start')?.addEventListener('click',()=>void runRumorHunter());
    rumorBox.querySelector('#hk-rumors-refresh')?.addEventListener('click',()=>void refreshRumorsPage());
    rumorBox.querySelector('#hk-rumors-copy')?.addEventListener('click',()=>void copyRumorsToday());
    rumorBox.querySelector('#hk-rumors-pause')?.addEventListener('click',()=>{if(hkRunner.state.status==='paused')hkRunner.resume();else hkRunner.pause();renderRumorsPage();});
    rumorBox.querySelector('#hk-rumors-stop')?.addEventListener('click',()=>hkRunner.stop('rumors-user-stop'));
    rumorBox.querySelectorAll('[data-rumor-area]').forEach(button=>button.addEventListener('click',()=>{
      const area=String(button.dataset.rumorArea||'');if(!area)return;
      runtime.navigate?.('maps');void openMapDetail(area,area);
    }));
    if(!state&&!rumorHunterRunning)void refreshRumorHunterState(false);
  }
'''
s=s[:a]+page+s[b:]

refresh_start="  async function refreshRumorsPage() {"
refresh_end="\n  async function loadDailyAccountAreas() {"
need(refresh_start,"refresh start"); need(refresh_end,"refresh end")
a=s.index(refresh_start); b=s.index(refresh_end,a)
refresh=r'''  async function refreshRumorsPage() {
    if(rumorBox&&!rumorHunterRunning)rumorBox.innerHTML='<p class="hk-muted">'+either('Обновляю слухи и координатор…','Refreshing rumors and coordinator…')+'</p>';
    await Promise.all([loadRumorRoute(),refreshRumorHunterState(false)]);
    renderRumorsTodaySummary();
    renderRumorsPage();
  }
'''
s=s[:a]+refresh+s[b:]

rep(
    "      if (finalPage === 'rumors') { renderRumorsPage(); if(!dailyRumorRoute.length)void refreshRumorsPage(); }",
    "      if (finalPage === 'rumors') { renderRumorsPage(); if(!dailyRumorRoute.length)void refreshRumorsPage(); else void refreshRumorHunterState(false); }",
    "rumors page activation"
)

css_anchor=".hk-rumor-summary-actions,.hk-rumor-actions{display:flex;gap:7px;flex-wrap:wrap}"
need(css_anchor,"rumor css anchor")
s=s.replace(
    css_anchor,
    ".hk-rumor-summary-city{padding:7px 8px;border:1px solid #26364a;border-radius:9px;background:#101927}.hk-rumor-summary-city>strong{display:block;margin-bottom:6px}.hk-rumor-summary-city>div{display:flex;gap:5px;flex-wrap:wrap}.hk-rumor-summary-point{display:grid;gap:2px;text-align:left;padding:6px 8px;border:1px solid #2e7058;border-radius:8px;background:#10231d;color:inherit}.hk-rumor-summary-point b{color:#7fe0ad;font:800 11px ui-monospace,monospace}.hk-rumor-summary-point small{font-size:8px;color:#8296aa}.hk-rumor-city-meta{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;margin-top:5px;color:#8496aa}.hk-rumor-history{margin-top:12px;border:1px solid #304057;border-radius:11px;background:#0d1621}.hk-rumor-history>summary{padding:9px 10px;cursor:pointer;font-weight:800}.hk-rumor-history>div{padding:0 8px 8px}.hk-rumor-history-row{display:grid;grid-template-columns:minmax(80px,.8fr) 1.5fr auto;gap:7px;align-items:center;padding:6px 4px;border-top:1px solid #203044}.hk-rumor-history-row:first-child{border-top:0}.hk-rumor-history-row small{color:#72849a;white-space:nowrap}"+css_anchor,
    1
)

mobile_anchor="@media(max-width:720px){.hk-rumor-summary-routes>div{grid-template-columns:1fr}"
need(mobile_anchor,"rumor mobile css")
s=s.replace(mobile_anchor,"@media(max-width:720px){.hk-rumor-history-row{grid-template-columns:1fr auto}.hk-rumor-history-row span{grid-column:1/3}.hk-rumor-summary-routes>div{grid-template-columns:1fr}",1)

for marker in [
    "// @version      1.18.15",
    "const BUILD_VERSION = '1.18.15';",
    "rumors-hunter-coordinator-kokkaras-v40-20260926-r4",
    "const RUMOR_HUNTER_RADIUS=3;",
    "class HKRumorCityHunter",
    "async function runRumorHunter()",
    "async function refreshRumorHunterState",
    "action:String(action||'state')",
    "lease_token:String(rumorHunterLease.lease_token||'')",
    "Сигнатура карты изменилась",
    "Kokkaras private coordinator is NOT used",
    "async function runDailyRumors(internal = false)",
    "treasure-run-recorder-stability-blockers-20260926-r2",
    "treasure-run-recorder-20260926-r1",
    "battle-visible-board-active-20260926-r1",
    "false zero is not stored.",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

target.write_text(s,encoding="utf-8")
print("RUMORS_HUNTER_FULL_1_18_15=PASS")
print("version=1.18.15")
# build trigger 20260926-r1
