from pathlib import Path
# deploy-trigger: verified 1.17.3 workflow

REV='regular-fair-ui-20260920-r1'
MARKER=f"HK_REGULAR_FAIR_REV = '{REV}'"

def require(text, needle, message):
    if needle not in text:
        raise SystemExit(message)

def replace_once(text, old, new, message):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(message)
    return text.replace(old,new,1)

def apply_hotfix(text):
    s=text
    if MARKER in s:
        s=s.replace('// @version      1.17.2','// @version      1.17.3',1)
        s=s.replace(": '1.17.2';",": '1.17.3';",1)
        return validate(s)

    require(s,'// @version      1.17.2','Regular Fair requires live 1.17.2')
    require(s,"HK_STAGE2J_BOSSES_REV = 'bosses-readonly-20260920-r1'",'Bosses 1.17.2 marker missing')
    require(s,"{planned:true,ru:'Обычная ярмарка',en:'Regular Fair'}",'Regular Fair planned nav anchor missing')
    require(s,"if (id === 'fair_default' || id === 'fair_event_base') return true;",'fair_default visibility anchor missing')
    require(s,"const visibleFairs = visibleFairStates();",'Fair load state anchor missing')
    require(s,"const states = visibleFairStates();",'Fair render state anchor missing')
    require(s,"const activateModule = (page,persist=true) => {",'Navigation activation anchor missing')

    s=s.replace('// @version      1.17.2','// @version      1.17.3',1)
    s=s.replace(": '1.17.2';",": '1.17.3';",1)

    boss_marker="  const HK_STAGE2J_BOSSES_REV = 'bosses-readonly-20260920-r1';"
    require(s,boss_marker,'Bosses runtime marker anchor missing')
    s=s.replace(boss_marker,boss_marker+"\n  const "+MARKER+";",1)

    # One engine, two views: the existing Fair remains unchanged; the new
    # Regular Fair navigation entry narrows that engine to fair_default only.
    anchor="  function userVisibleFair(state) {"
    require(s,anchor,'userVisibleFair anchor missing')
    s=s.replace(anchor,"  let fairViewMode = 'all';\n\n"+anchor,1)

    old="""  function visibleFairStates(documentValue = fairDocument || playerDocument) {
    return fairStates(documentValue).filter(state => userVisibleFair(state) && fairRowsForState(state).length);
  }"""
    new="""  function visibleFairStates(documentValue = fairDocument || playerDocument) {
    return fairStates(documentValue).filter(state => userVisibleFair(state) && fairRowsForState(state).length);
  }

  function fairStatesForView(documentValue = fairDocument || playerDocument) {
    const states = visibleFairStates(documentValue);
    if (fairViewMode === 'regular') return states.filter(state => String(state?.id || '') === 'fair_default');
    return states;
  }"""
    s=replace_once(s,old,new,'Fair view helper anchor missing')

    s=s.replace("const visibleFairs = visibleFairStates();","const visibleFairs = fairStatesForView();",1)
    s=s.replace("const states = visibleFairStates();","const states = fairStatesForView();",1)

    s=replace_once(
        s,
        "{page:'fair',ru:'Ярмарка',en:'Fair'},{page:'shop',ru:'Магазин',en:'Shop'},{planned:true,ru:'Обычная ярмарка',en:'Regular Fair'}",
        "{page:'fair',ru:'Ярмарка',en:'Fair'},{page:'shop',ru:'Магазин',en:'Shop'},{page:'fair-regular',ru:'Обычная ярмарка',en:'Regular Fair'}",
        'Regular Fair nav replacement missing'
    )

    old="""    const activateModule = (page,persist=true) => {
      const target=root.querySelector(`[data-content="${page}"]`) || root.querySelector('[data-content="daily"]');
      const finalPage=target.dataset.content;
      const group=groupForPage(finalPage);
      root.querySelectorAll('.hk-tab').forEach(button=>button.classList.toggle('active',button.dataset.group===group.id));
      root.querySelectorAll('.hk-page').forEach(section=>section.classList.toggle('active',section===target));
      renderGroupSubnav(group.id,finalPage);
      if(persist) save({navGroup:group.id,navModule:finalPage});"""
    new="""    const activateModule = (page,persist=true) => {
      const regularFairAlias = page === 'fair-regular';
      const contentPage = regularFairAlias ? 'fair' : page;
      const target=root.querySelector(`[data-content="${contentPage}"]`) || root.querySelector('[data-content="daily"]');
      const finalPage=target.dataset.content;
      const navPage=regularFairAlias ? 'fair-regular' : finalPage;
      const group=groupForPage(navPage);
      root.querySelectorAll('.hk-tab').forEach(button=>button.classList.toggle('active',button.dataset.group===group.id));
      root.querySelectorAll('.hk-page').forEach(section=>section.classList.toggle('active',section===target));
      renderGroupSubnav(group.id,navPage);
      if(persist) save({navGroup:group.id,navModule:navPage});"""
    s=replace_once(s,old,new,'activateModule alias anchor missing')

    old="      if (finalPage === 'fair') renderFair();"
    new="""      if (finalPage === 'fair') {
        fairViewMode = regularFairAlias ? 'regular' : 'all';
        if (regularFairAlias) {
          selectedFairId = 'fair_default';
          selectedFairLots.clear();
          selectedFairSlotRules.clear();
          selectedFairCurrency = '';
        }
        renderFair();
      }"""
    s=replace_once(s,old,new,'Fair activation anchor missing')

    old="""    const remembered=clean(load().navModule||'daily');
    activateModule(root.querySelector(`[data-content="${remembered}"]`)?remembered:'daily',false);"""
    new="""    const remembered=clean(load().navModule||'daily');
    activateModule(remembered === 'fair-regular' || root.querySelector(`[data-content="${remembered}"]`) ? remembered : 'daily',false);"""
    s=replace_once(s,old,new,'Remembered navigation anchor missing')

    return validate(s)

def validate(s):
    checks=[
        '// @version      1.17.3',
        ": '1.17.3';",
        MARKER,
        "{page:'fair-regular',ru:'Обычная ярмарка',en:'Regular Fair'}",
        "let fairViewMode = 'all';",
        "function fairStatesForView(",
        "fairViewMode === 'regular'",
        "String(state?.id || '') === 'fair_default'",
        "const regularFairAlias = page === 'fair-regular';",
        "const contentPage = regularFairAlias ? 'fair' : page;",
        "const navPage=regularFairAlias ? 'fair-regular' : finalPage;",
        "selectedFairId = 'fair_default';",
        "remembered === 'fair-regular'",
        "budgetDecision(row.cost, 'fair', 1, playerDocument",
        "HK_NATIVE_LOGIN_GATE_V1 login-gate-20260920-r1",
        "HK_BUREAU_RESOURCES_LIVE_V1 bureau-resources-live-20260920-r1",
        "GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",
        "GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",
    ]
    for needle in checks:
        require(s,needle,f'Regular Fair validation missing: {needle}')
    if "{planned:true,ru:'Обычная ярмарка',en:'Regular Fair'}" in s:
        raise SystemExit('Regular Fair is still planned')
    return s

if __name__ == '__main__':
    p=Path('/tmp/HamsterKingMobile.user.js')
    s=p.read_text(encoding='utf-8')
    p.write_text(apply_hotfix(s),encoding='utf-8')
    print('HK_REGULAR_FAIR_1173_OK')
