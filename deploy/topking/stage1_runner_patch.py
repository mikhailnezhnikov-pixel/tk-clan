from pathlib import Path
p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')
s=s.replace('// @version      1.14.4','// @version      1.15.0',1)
s=s.replace(": '1.14.4';",": '1.15.0';",1)
old="  async function apiJson(path, method = 'GET', body = null, retryAuthorization = true, retryNetwork = 3) {"
if old not in s: raise SystemExit('apiJson signature not found')
s=s.replace(old,"  async function apiJsonCore(path, method = 'GET', body = null, retryAuthorization = true, retryNetwork = 3) {",1)
marker="\n  function deepObjects(value, depth = 0, output = []) {"
if marker not in s: raise SystemExit('deepObjects marker not found')
gate=r'''
  const HK_READ_ONLY_POST_PATHS = new Set([
    '/player/me','/player/hamster/lvlUp/view','/shop/view','/business/values',
    '/business_items','/cities','/client_config','/events','/items','/leaderboard',
    '/premium','/bonuses/view','/alliance/list','/clan/skill_lines/stats','/player/event'
  ]);
  const hkMutationGate = (() => {
    let tail = Promise.resolve();
    let sequence = 0;
    let active = null;
    const state = {pending:0, completed:0, failed:0, lastPath:'', activePath:''};
    const run = async (path, task) => {
      const id = ++sequence;
      state.pending++;
      let release;
      const turn = new Promise(resolve => { release = resolve; });
      const previous = tail;
      tail = turn;
      await previous.catch(() => {});
      state.pending = Math.max(0,state.pending-1);
      state.activePath = String(path||'');
      active = {id,path:state.activePath,startedAt:Date.now()};
      recordDiagnostic('mutation-start',{id,path:state.activePath,pending:state.pending});
      try {
        if (hkRunner.running) await hkRunner.waitIfPaused();
        const value = await task();
        state.completed++;
        recordDiagnostic('mutation-finish',{id,path:state.activePath,durationMs:Date.now()-active.startedAt});
        return value;
      } catch (error) {
        state.failed++;
        recordDiagnostic('mutation-error',{id,path:state.activePath,error:error?.message||String(error)});
        throw error;
      } finally {
        active = null; state.activePath=''; release();
      }
    };
    return {state,run,get active(){return active;}};
  })();

  function hkIsMutationRequest(path,method='GET'){
    const verb=String(method||'GET').toUpperCase();
    if(verb==='GET'||verb==='HEAD'||verb==='OPTIONS')return false;
    return !HK_READ_ONLY_POST_PATHS.has(String(path||''));
  }

  async function apiJson(path, method = 'GET', body = null, retryAuthorization = true, retryNetwork = 3) {
    if(!hkIsMutationRequest(path,method)) return apiJsonCore(path,method,body,retryAuthorization,retryNetwork);
    return hkMutationGate.run(path,()=>apiJsonCore(path,method,body,retryAuthorization,retryNetwork));
  }
'''
s=s.replace(marker,"\n"+gate+marker,1)
runtime_marker="  runtime.runner = hkRunner;"
if runtime_marker not in s: raise SystemExit('runtime runner marker not found')
s=s.replace(runtime_marker,runtime_marker+"\n  runtime.mutationGate = hkMutationGate;",1)
p.write_text(s,encoding='utf-8')
