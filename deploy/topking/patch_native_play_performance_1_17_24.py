from pathlib import Path

PATH = Path("/tmp/HamsterKingMobile.user.js")
s = PATH.read_text(encoding="utf-8")

def replace_once(old,new,label):
    global s
    count=s.count(old)
    if count!=1:
        raise SystemExit(f"{label}: expected 1 match, got {count}")
    s=s.replace(old,new,1)

for marker in [
    "native-game-priority-no-bridge-race-20260921-r1",
    "puzzle-solver-v3-embedded-20260921-r1",
    "businesses-finalize-single-snapshot-20260921-r1",
    "function setHealth(name, ok, detail = '')",
    "function acceptSharedGameResponse(url,documentValue)",
    "function acceptPlayerState(url, headers, documentValue, partial = false)",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

release="// @release-note Исправлена совместимость с обычной игрой: HK больше не запускает дополнительное обновление player state после нативных действий пользователя."
replace_once(
    release,
    "// @release-note Убраны фоновые лаги: тяжёлый DOM-скан Ям больше не выполняется каждую секунду, а Бизнесы не перерисовываются после каждого нативного действия игры.\n"+release,
    "performance release note"
)

health_old="""  function setHealth(name, ok, detail = '') {
    if (!healthState[name]) return;
    healthState[name] = {ok:!!ok, detail:clean(detail || (ok ? 'OK' : 'ошибка'))};
    renderHealth();
  }"""
health_new="""  function setHealth(name, ok, detail = '') {
    if (!healthState[name]) return;
    const next={ok:!!ok, detail:clean(detail || (ok ? 'OK' : 'ошибка'))};
    const current=healthState[name];
    if(current?.ok===next.ok && current?.detail===next.detail) return;
    healthState[name]=next;
    renderHealth();
  }

  const HK_NATIVE_PLAY_PERF_REV='native-play-performance-20260921-r1';
  function hkPanelOpen(){return !!panel?.classList?.contains('open');}
  function hkActiveModule(){return root?.querySelector?.('.hk-page.active')?.dataset?.content || '';}
  function hkBusinessUiVisible(){return hkPanelOpen() && hkActiveModule()==='business';}
  function hkPitUiVisible(){return hkPanelOpen() && hkActiveModule()==='pit';}"""
replace_once(health_old,health_new,"health dedupe + visibility helpers")

replace_once(
    """    if(hkStateStore.revision!==before&&merged){playerDocument=merged;try{refreshBusinessData();}catch(_){}}""",
    """    if(hkStateStore.revision!==before&&merged){
      playerDocument=merged;
      if(hkBusinessUiVisible())try{refreshBusinessData();}catch(_){}
    }""",
    "shared native response business redraw gate"
)

replace_once(
    """    refreshBusinessData();
    const player = playerDocument.player || {};""",
    """    if(hkBusinessUiVisible()) refreshBusinessData();
    const player = playerDocument.player || {};""",
    "player me business redraw gate"
)

tick_old="""    setInterval(() => {
      updatePitStatus();
      const c=root.querySelector('#hk-connect'); if(c)c.textContent=apiHeaders.Authorization?tr('connectedSlots',{n:layout.length}):tr('waiting');
      const token=currentGameBearer(); const exp=jwtExpiration(token);
      setHealth('auth', !!token && exp > Date.now()+5000, token ? (exp > Date.now()+5000 ? 'авторизация активна' : 'токен истёк') : 'нет токена');
    }, 1000);"""
tick_new="""    setInterval(() => {
      // The old global 1-second tick called pitState() on every screen.
      // pitState() reads document.body.innerText and scans all buttons/links,
      // which caused a visible rhythmic hitch even while simply playing.
      if(pitRunning || hkPitUiVisible()) updatePitStatus();
      const c=root.querySelector('#hk-connect');
      if(c){
        const next=apiHeaders.Authorization?tr('connectedSlots',{n:layout.length}):tr('waiting');
        if(c.textContent!==next)c.textContent=next;
      }
      const token=currentGameBearer(); const exp=jwtExpiration(token);
      setHealth('auth', !!token && exp > Date.now()+5000, token ? (exp > Date.now()+5000 ? 'авторизация активна' : 'токен истёк') : 'нет токена');
    }, 5000);"""
replace_once(tick_old,tick_new,"global heartbeat performance")

for marker in [
    "HK_NATIVE_PLAY_PERF_REV='native-play-performance-20260921-r1'",
    "function hkBusinessUiVisible()",
    "function hkPitUiVisible()",
    "if(hkBusinessUiVisible()) refreshBusinessData();",
    "if(pitRunning || hkPitUiVisible()) updatePitStatus();",
    "}, 5000);",
    "native-game-priority-no-bridge-race-20260921-r1",
    "puzzle-solver-v3-embedded-20260921-r1",
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

# Guard against regression: there must be no unconditional global 1-second pit refresh.
if """setInterval(() => {
      updatePitStatus();""" in s:
    raise SystemExit("unconditional 1-second pit scan still present")

PATH.write_text(s,encoding="utf-8")
print("NATIVE_PLAY_PERFORMANCE_R1=PASS")
