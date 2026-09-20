from pathlib import Path

p=Path('/tmp/HamsterKingMobile.user.js')
s=p.read_text(encoding='utf-8')

BASE="const HK_PITS_PROGRESS_REV = 'pits-battle-progress-20260920-r8';"
MARK="const HK_PITS_RUNNER_HISTORY_REV = 'pits-runner-history-20260920-r9';"
if MARK in s:
    raise SystemExit('already applied')
if BASE not in s:
    raise SystemExit('r8 marker missing')
s=s.replace(BASE, BASE+"\n  "+MARK, 1)

old="    const state = {status:'idle', title:'', step:'', done:0, total:0, startedAt:0, error:'', pausable:true, stoppable:true};"
new="    const state = {status:'idle', title:'', step:'', done:0, total:0, startedAt:0, error:'', pausable:true, stoppable:true, history:[]};"
if old not in s: raise SystemExit('runner state anchor missing')
s=s.replace(old,new,1)

old="        Object.assign(state,{status:'running',title:String(title||either('Выполнение','Execution')),step:String(step||''),done:0,total:Math.max(0,Number(total)||0),startedAt:Date.now(),error:'',pausable:!!pausable,stoppable:!!stoppable});"
new="        Object.assign(state,{status:'running',title:String(title||either('Выполнение','Execution')),step:String(step||''),done:0,total:Math.max(0,Number(total)||0),startedAt:Date.now(),error:'',pausable:!!pausable,stoppable:!!stoppable,history:[]});"
if old not in s: raise SystemExit('runner start anchor missing')
s=s.replace(old,new,1)

anchor="      setStep(step, done=state.done, total=state.total) { state.step=String(step||''); state.done=Math.max(0,Number(done)||0); state.total=Math.max(0,Number(total)||0); emit(); return state; },\n"
insert=anchor+"      note(message,type='') { const value=String(message||'').trim(); if(!value)return state; const safeType=['ok','warn','bad','info'].includes(type)?type:''; state.history=[...(state.history||[]),{text:value,type:safeType,at:Date.now()}].slice(-10); emit(); return state; },\n"
if anchor not in s: raise SystemExit('runner setStep anchor missing')
s=s.replace(anchor,insert,1)

old="      reset() { abortController=null; settlePaused(); Object.assign(state,{status:'idle',title:'',step:'',done:0,total:0,startedAt:0,error:'',pausable:true,stoppable:true}); emit(); }"
new="      reset() { abortController=null; settlePaused(); Object.assign(state,{status:'idle',title:'',step:'',done:0,total:0,startedAt:0,error:'',pausable:true,stoppable:true,history:[]}); emit(); }"
if old not in s: raise SystemExit('runner reset anchor missing')
s=s.replace(old,new,1)

old="""    const visibleState=state.status!=='idle'; box.classList.toggle('show',visibleState);
    if(!visibleState)return;
"""
new="""    const visibleState=state.status!=='idle'; box.classList.toggle('show',visibleState);
    box.classList.toggle('pit-run',visibleState&&String(state.title||'')===either('Ямы','Pits'));
    if(!visibleState)return;
"""
if old not in s: raise SystemExit('runner visible anchor missing')
s=s.replace(old,new,1)

pause_anchor="    const pause=root.querySelector('#hk-runner-pause'); const stop=root.querySelector('#hk-runner-stop');"
history_render="""    const history=root.querySelector('#hk-runner-history');
    if(history){
      const rows=Array.isArray(state.history)?state.history:[];
      history.innerHTML=rows.map(row=>'<div class="hk-runner-history-row '+escapeHtml(row.type||'')+'"><span>'+new Date(row.at||Date.now()).toLocaleTimeString(locale(),{hour:'2-digit',minute:'2-digit',second:'2-digit'})+'</span><b>'+escapeHtml(row.text||'')+'</b></div>').join('');
      history.style.display=rows.length?'grid':'none';
    }
"""
if pause_anchor not in s: raise SystemExit('runner pause anchor missing')
s=s.replace(pause_anchor,history_render+pause_anchor,1)

old_html='<div id="hk-runner-step" class="hk-runner-step"></div><div class="hk-runner-track"><div id="hk-runner-fill" class="hk-runner-fill"></div></div><div class="hk-runner-actions">'
new_html='<div id="hk-runner-step" class="hk-runner-step"></div><div class="hk-runner-track"><div id="hk-runner-fill" class="hk-runner-fill"></div></div><div id="hk-runner-history" class="hk-runner-history" style="display:none"></div><div class="hk-runner-actions">'
if old_html not in s: raise SystemExit('runner html anchor missing')
s=s.replace(old_html,new_html,1)

old_css=".hk-runner{display:none;margin:0 0 12px;padding:11px;border:1px solid #36506f;border-radius:14px;background:linear-gradient(145deg,#111c2a,#0d1520)}.hk-runner.show{display:block}"
new_css=".hk-runner{display:none;margin:0 0 12px;padding:11px;border:1px solid #36506f;border-radius:14px;background:linear-gradient(145deg,#111c2a,#0d1520)}.hk-runner.show{display:block}.hk-runner.pit-run{border-color:#ffad1f;background:linear-gradient(145deg,#302411,#17170f);box-shadow:0 0 0 2px #ffad1f26,0 8px 24px #0006}"
if old_css not in s: raise SystemExit('runner css anchor missing')
s=s.replace(old_css,new_css,1)

old_css=".hk-runner-actions{display:flex;gap:7px}.hk-runner-actions button{flex:1;min-height:34px;font-size:11px}"
new_css=".hk-runner-history{display:grid;gap:4px;max-height:290px;overflow:auto;margin:8px 0;padding:8px;border:1px solid #5a4724;border-radius:10px;background:#080b0f99}.hk-runner-history-row{display:grid;grid-template-columns:58px minmax(0,1fr);gap:7px;align-items:start;padding:4px 6px;border-radius:7px;background:#ffffff05}.hk-runner-history-row span{color:#7f8b9d;font:9px ui-monospace,monospace}.hk-runner-history-row b{font-size:10px;line-height:1.25;color:#dce5f1}.hk-runner-history-row.ok b{color:#7fe0ad}.hk-runner-history-row.warn b{color:#ffd166}.hk-runner-history-row.bad b{color:#ff8995}.hk-runner-history-row.info b{color:#a9c9ff}.hk-runner-actions{display:flex;gap:7px}.hk-runner-actions button{flex:1;min-height:34px;font-size:11px}"
if old_css not in s: raise SystemExit('runner actions css anchor missing')
s=s.replace(old_css,new_css,1)

helper_anchor="  async function pitCanonRunOne(config,progress) {"
helper="  function pitCanonRunnerLog(message,type='') { log(message,type); hkRunner.note(message,type); }\n\n"
if helper_anchor not in s: raise SystemExit('pit run anchor missing')
s=s.replace(helper_anchor,helper+helper_anchor,1)

start=s.find("  async function pitCanonRunOne(config,progress) {")
end=s.find("\n  function ",s.find("  async function runPitsCanonical()",start)+10)
if start<0: raise SystemExit('pitCanonRunOne missing after helper insert')
if end<0: end=len(s)
block=s[start:end]
if "log(" not in block: raise SystemExit('no Pits logs found in run block')
block=block.replace("log(","pitCanonRunnerLog(")
s=s[:start]+block+s[end:]

for needle in [
    MARK,
    "history:[]",
    "note(message,type='')",
    'id="hk-runner-history"',
    ".hk-runner.pit-run",
    "function pitCanonRunnerLog(message,type='')",
    "pitCanonRunnerLog("
]:
    if needle not in s:
        raise SystemExit('missing r9 invariant: '+needle)

p.write_text(s,encoding='utf-8')
print('PITS_RUNNER_HISTORY_R9_PATCH_OK')
