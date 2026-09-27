from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count:
        raise SystemExit(f"{label}: expected {count} got {n}")
    s=s.replace(old,new,count)

rep("// @version      1.18.53",
    "// @version      1.18.54\n// @release-note Сражения: добавлен разовый приоритет двух достижений. Пока достижение не отмечено выполненным, Автобой заранее моделирует цепочки зелёных/синих врагов и, если это достижимо текущими мечами, сначала пытается довести HP одного живого врага до 16+ и отдельно общую сумму HP живых врагов до 68+. После фактического достижения условие запоминается для аккаунта; если игра уже показывает достижение выполненным, специальный режим пропускается. Если подходящей цепочки нет, бой идёт обычным оптимальным маршрутом.",
    "version")
rep("const BUILD_VERSION = '1.18.53';",
    "const BUILD_VERSION = '1.18.54';",
    "build")
rep("  const HK_BATTLE_RAW_CONTEXT_REV='battle-raw-context-mobile-tap-20260927-r1';",
    "  const HK_BATTLE_RAW_CONTEXT_REV='battle-raw-context-mobile-tap-20260927-r1';\n  const HK_BATTLE_ACHIEVEMENT_REV='battle-achievement-priority-20260927-r1';",
    "revision")

rep("    const BATTLE_AUTO_STORAGE_KEY = 'hk:battle:auto-click:v1';\n    const CHEST_AUTO_STORAGE_KEY = 'hk:chests:auto-open:v1';",
    "    const BATTLE_AUTO_STORAGE_KEY = 'hk:battle:auto-click:v1';\n    const BATTLE_ACHIEVEMENT_STORAGE_KEY = 'hk:treasure:battle-achievements:v1';\n    const CHEST_AUTO_STORAGE_KEY = 'hk:chests:auto-open:v1';",
    "achievement storage key")

anchor="""    function runBattle() {
"""
helper=r"""    function battleAchievementStorageKey() {
      const playerId=clean(
        licenseState.playerId ||
        playerIdentity(playerDocument?.player || {}) ||
        'unknown'
      );
      return BATTLE_ACHIEVEMENT_STORAGE_KEY+':'+playerId;
    }

    function battleAchievementLocalState() {
      try {
        const value=JSON.parse(localStorage.getItem(battleAchievementStorageKey())||'{}');
        return value && typeof value==='object' ? value : {};
      } catch (_) {
        return {};
      }
    }

    function battleAchievementMark(kind,reason='observed',metrics={}) {
      if (kind!=='hp16' && kind!=='total68') return false;
      const current=battleAchievementLocalState();
      if (current[kind]===true) return true;
      current[kind]=true;
      current[kind+'At']=Date.now();
      current[kind+'Reason']=String(reason||'observed');
      try {
        localStorage.setItem(battleAchievementStorageKey(),JSON.stringify(current));
      } catch (_) {}
      recordDiagnostic('battle-achievement-complete',{
        revision:HK_BATTLE_ACHIEVEMENT_REV,
        kind,
        reason:String(reason||'observed'),
        ...metrics
      });
      return true;
    }

    function battleAchievementRemoteComplete(kind) {
      const cache=battleAchievementRemoteComplete.cache ||
        (battleAchievementRemoteComplete.cache={at:0,hp16:null,total68:null});
      const now=Date.now();
      if (now-cache.at<15000 && cache[kind]!==null) return cache[kind]===true;

      const found={hp16:false,total68:false};
      const seen=new WeakSet();
      let visited=0;

      const completionValue=value=>{
        if (value===true || value===1 || value==='1') return true;
        const text=String(value??'').toLowerCase();
        return /^(?:completed|claimed|done|unlocked|complete|finished|выполнено|получено|открыто)$/.test(text);
      };

      const inspectObject=(value,path)=>{
        if (!value || typeof value!=='object' || Array.isArray(value)) return;
        const keys=Object.keys(value);
        const scalar=[];
        for (const key of keys) {
          const item=value[key];
          if (item==null || ['string','number','boolean'].includes(typeof item)) {
            scalar.push(key+'='+String(item));
          }
        }
        const text=(path+' '+scalar.join(' ')).toLowerCase();
        if (!/(?:achiev|достиж)/.test(text)) return;

        let complete=false;
        for (const key of keys) {
          if (!/(?:completed|claimed|done|unlocked|finished|is_complete|is_completed|is_claimed|is_done|is_unlocked)/i.test(key)) continue;
          if (completionValue(value[key])) { complete=true; break; }
        }
        if (!complete && /(?:status|state)=?(?:completed|claimed|done|unlocked|finished)/i.test(text)) complete=true;
        if (!complete) return;

        const hpText=/(?:hp|health|здоров|хп)/i.test(text);
        if (!hpText) return;
        if (/(?:^|\D)16(?:\D|$)/.test(text)) found.hp16=true;
        if (/(?:^|\D)68(?:\D|$)/.test(text)) found.total68=true;
      };

      const walk=(value,path='$',depth=0)=>{
        if (!value || typeof value!=='object' || depth>8 || visited>=6000) return;
        if (seen.has(value)) return;
        seen.add(value);
        visited+=1;
        inspectObject(value,path);
        if (Array.isArray(value)) {
          for (let i=0;i<value.length && visited<6000;i++) {
            if (value[i] && typeof value[i]==='object') walk(value[i],path+'['+i+']',depth+1);
          }
          return;
        }
        for (const key of Object.keys(value)) {
          const child=value[key];
          if (child && typeof child==='object') walk(child,path+'.'+key,depth+1);
          if (visited>=6000) break;
        }
      };

      walk(playerDocument,'$.playerDocument');
      if (fairDocument && fairDocument!==playerDocument) walk(fairDocument,'$.fairDocument');

      try {
        const rows=[...document.querySelectorAll(
          '[data-lot-id*="achievement"],[class*="achievement"],[id*="achievement"]'
        )].filter(visible);
        for (const row of rows) {
          const text=clean(row.innerText||row.textContent||'').toLowerCase();
          const cls=String(row.className||'').toLowerCase();
          const done=/(?:completed|claimed|done|unlocked|finished|выполнено|получено|открыто|✓)/i.test(text+' '+cls);
          if (!done || !/(?:hp|health|здоров|хп)/i.test(text)) continue;
          if (/(?:^|\D)16(?:\D|$)/.test(text)) found.hp16=true;
          if (/(?:^|\D)68(?:\D|$)/.test(text)) found.total68=true;
        }
      } catch (_) {}

      cache.at=now;
      cache.hp16=found.hp16;
      cache.total68=found.total68;
      return found[kind]===true;
    }

    function battleAchievementDone(kind) {
      const local=battleAchievementLocalState();
      if (local[kind]===true) return true;
      if (battleAchievementRemoteComplete(kind)) {
        battleAchievementMark(kind,'game-completed');
        return true;
      }
      return false;
    }

    function battleAchievementMetrics(state) {
      let totalHp=0;
      let maxHp=0;
      let alive=0;
      (state||[]).forEach(enemy=>{
        if (!enemy || !enemy.alive) return;
        const hp=Math.max(0,Number(enemy.hp)||0);
        totalHp+=hp;
        maxHp=Math.max(maxHp,hp);
        alive+=1;
      });
      return {totalHp,maxHp,alive};
    }

    function battleAchievementObserveState(state) {
      const metrics=battleAchievementMetrics(state);
      if (metrics.maxHp>=16 && !battleAchievementDone('hp16')) {
        battleAchievementMark('hp16','battle-state-observed',metrics);
      }
      if (metrics.totalHp>=68 && !battleAchievementDone('total68')) {
        battleAchievementMark('total68','battle-state-observed',metrics);
      }
      return metrics;
    }

    function battleAchievementReached(kind,state) {
      const {totalHp,maxHp}=battleAchievementMetrics(state);
      if (kind==='hp16') return maxHp>=16;
      if (kind==='total68') return totalHp>=68;
      return false;
    }

    function solveBattleAchievement(initialState,maxAttack,kind) {
      if (!Array.isArray(initialState) || !Number.isFinite(maxAttack) || maxAttack<0) return null;
      if (kind!=='hp16' && kind!=='total68') return null;
      if (battleAchievementReached(kind,initialState)) {
        return {killed:0,cost:0,order:[],mode:'achievement-'+kind,visited:0};
      }

      const maxDepth=8;
      const queue=[{
        state:copyBattleState(initialState),
        remaining:maxAttack,
        order:[],
        cost:0
      }];
      const seen=new Set();
      let head=0;
      let visited=0;
      const initialAlive=countBattleAlive(initialState);

      while (head<queue.length && visited<6000) {
        const node=queue[head++];
        visited+=1;
        if (node.order.length>=maxDepth) continue;

        const key=battleStateKey(node.state)+'#'+node.remaining+'#'+node.order.length;
        if (seen.has(key)) continue;
        seen.add(key);

        for (let position=0;position<BATTLE_SIZE;position++) {
          const enemy=node.state[position];
          if (!enemy || !enemy.alive || enemy.hp<=0 || enemy.hp>node.remaining) continue;

          // Only GREEN deaths heal neighbours. BLUE may trigger a GREEN death
          // by explosion; RED can only reduce the metrics we are trying to grow.
          if (enemy.type!==GREEN && enemy.type!==BLUE) continue;

          const result=battleAttack(node.state,position);
          if (!result) continue;

          const next={
            state:result.state,
            remaining:node.remaining-result.cost,
            order:node.order.concat(position),
            cost:node.cost+result.cost
          };

          if (battleAchievementReached(kind,next.state)) {
            return {
              killed:initialAlive-countBattleAlive(next.state),
              cost:next.cost,
              order:next.order,
              mode:'achievement-'+kind,
              visited
            };
          }

          if (next.order.length<maxDepth) queue.push(next);
        }
      }

      recordDiagnostic('battle-achievement-plan-missing',{
        revision:HK_BATTLE_ACHIEVEMENT_REV,
        kind,
        swords:maxAttack,
        visited
      });
      return null;
    }

    function battleAchievementPlan(state,maxAttack) {
      const pending=[
        ['hp16','16 HP'],
        ['total68','68 HP']
      ];
      for (const [kind,label] of pending) {
        if (battleAchievementDone(kind)) continue;
        const plan=solveBattleAchievement(state,maxAttack,kind);
        if (!plan || !plan.order.length) continue;
        const predicted=copyBattleState(state);
        let simulated=predicted;
        let remaining=maxAttack;
        for (const position of plan.order) {
          const step=battleAttack(simulated,position);
          if (!step || step.cost>remaining) break;
          remaining-=step.cost;
          simulated=step.state;
        }
        const metrics=battleAchievementMetrics(simulated);
        recordDiagnostic('battle-achievement-plan',{
          revision:HK_BATTLE_ACHIEVEMENT_REV,
          kind,
          label,
          swords:maxAttack,
          cost:plan.cost,
          order:plan.order.map(position=>position+BATTLE_FIRST_SLOT),
          predictedMaxHp:metrics.maxHp,
          predictedTotalHp:metrics.totalHp,
          visited:plan.visited
        });
        return plan;
      }
      return null;
    }

"""
if s.count(anchor)!=1:
    raise SystemExit("runBattle anchor missing")
s=s.replace(anchor,helper+anchor,1)

old_run="""      clearNumbers();
      const state = board.map(enemy => enemy ? {type:enemy.type,hp:enemy.hp,alive:true} : null);
      const totalHp=state.reduce((sum,enemy)=>sum+(enemy&&enemy.alive?Math.max(0,Number(enemy.hp)||0):0),0);
      const solution = solveBattle(state,maxAttack);
      const solverKilled=Number(solution?.killed||0);

      if (!solution || solution.order.length===0) {
"""
new_run="""      clearNumbers();
      const state = board.map(enemy => enemy ? {type:enemy.type,hp:enemy.hp,alive:true} : null);
      const observedMetrics=battleAchievementObserveState(state);
      const totalHp=observedMetrics.totalHp;

      let solution=battleAchievementPlan(state,maxAttack);
      if (!solution) solution=solveBattle(state,maxAttack);
      const solutionMode=solution?.mode||'normal';
      const solverKilled=Number(solution?.killed||0);

      if (solutionMode==='achievement-hp16' && autoMapEnabled()) {
        autoMapStatus('достижение 16 HP',{revision:HK_BATTLE_ACHIEVEMENT_REV});
      } else if (solutionMode==='achievement-total68' && autoMapEnabled()) {
        autoMapStatus('достижение 68 HP',{revision:HK_BATTLE_ACHIEVEMENT_REV});
      }

      if (!solution || solution.order.length===0) {
"""
rep(old_run,new_run,"integrate achievement plan")

rep("""      console.log('HK BATTLE ATK:',maxAttack);
      console.log('HK BATTLE HP:',totalHp);
      console.log('HK BATTLE потрачено:',solution.cost);
""",
    """      console.log('HK BATTLE ATK:',maxAttack);
      console.log('HK BATTLE HP:',totalHp);
      console.log('HK BATTLE режим:',solution.mode||'normal');
      console.log('HK BATTLE потрачено:',solution.cost);
""",
    "battle achievement mode log")

rep("""      recordDiagnostic('battle-auto-start',{
        revision:HK_BATTLE_MODAL_CONFIRM_REV,
        plannedSteps:solution.order.length,
        nextSlot:slot,
        fullOrder:solution.order.map(value=>value+BATTLE_FIRST_SLOT)
      });
""",
    """      recordDiagnostic('battle-auto-start',{
        revision:HK_BATTLE_MODAL_CONFIRM_REV,
        mode:String(solution.mode||'normal'),
        plannedSteps:solution.order.length,
        nextSlot:slot,
        fullOrder:solution.order.map(value=>value+BATTLE_FIRST_SLOT)
      });
""",
    "battle achievement auto mode")

rep("      battleRawContextRevision:HK_BATTLE_RAW_CONTEXT_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "      battleRawContextRevision:HK_BATTLE_RAW_CONTEXT_REV,\n      battleAchievementRevision:HK_BATTLE_ACHIEVEMENT_REV,\n      traderWhitelistRevision:HK_TRADER_WHITELIST_REV,",
    "export battle achievement revision")

for marker in [
    "// @version      1.18.54",
    "const BUILD_VERSION = '1.18.54';",
    "battle-achievement-priority-20260927-r1",
    "hk:treasure:battle-achievements:v1",
    "function battleAchievementStorageKey()",
    "function battleAchievementRemoteComplete(",
    "function solveBattleAchievement(",
    "function battleAchievementPlan(",
    "kind==='hp16'",
    "kind==='total68'",
    "maxHp>=16",
    "totalHp>=68",
    "enemy.type!==GREEN && enemy.type!==BLUE",
    "visited<6000",
    "maxDepth=8",
    "battleAchievementObserveState(state);",
    "let solution=battleAchievementPlan(state,maxAttack);",
    "if (!solution) solution=solveBattle(state,maxAttack);",
    "solution.mode||'normal'",
    "mode:String(solution.mode||'normal')",
    "battle-raw-context-mobile-tap-20260927-r1",
    "battle-strict-exit-gate-20260927-r1"
]:
    if marker not in s:
        raise SystemExit("missing "+marker)

p.write_text(s,encoding="utf-8")
print("TREASURE_BATTLE_ACHIEVEMENTS_1_18_54=PASS")
