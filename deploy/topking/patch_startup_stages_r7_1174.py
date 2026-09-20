from pathlib import Path

TARGET=Path('/tmp/HamsterKingMobile.user.js')
REV='startup-stages-20260920-r7'
MARKER=f"HK_STARTUP_STAGE_REV = '{REV}'"

def require(s,n,l):
    if n not in s: raise SystemExit(f'startup stage check failed: {l}')
def rep(s,o,n,l):
    if n in s: return s
    if o not in s: raise SystemExit(f'startup stage anchor missing: {l}')
    return s.replace(o,n,1)

def apply(s):
    require(s,"HK_CORE_REVISION = 'core-20260920-r6'",'core r6')
    if MARKER in s: return validate(s)

    s=rep(s,
        "  let bootstrapProblem = '';\n  let bootstrapButton = null;",
        "  const "+MARKER+";\n  let hkStartupStage = 'BOOT';\n  let bootstrapProblem = '';\n  let bootstrapButton = null;",
        'startup stage state')

    s=rep(s,
        "    bootstrapProblem = String(problem || bootstrapProblem || 'Ожидаю вход в игру…');",
        "    bootstrapProblem = String(problem || bootstrapProblem || ('HK '+HK_CORE_REVISION+' · '+hkStartupStage));",
        'diagnostic default message')

    s=rep(s,
        "      bootstrapButton.onclick = () => alert(bootstrapProblem);",
        "      bootstrapButton.onclick = () => alert(bootstrapProblem+'\\nrev='+HK_CORE_REVISION+'\\nstage='+hkStartupStage);",
        'diagnostic click')

    s=rep(s,
        "    bootstrapButton.textContent = problem ? 'HK!' : 'HK…';",
        "    bootstrapButton.textContent = problem ? 'HK!' : 'HK6';",
        'visible revision button')

    s=rep(s,
        "  function startInterface() {\n    if (root?.isConnected && root.querySelector('#hk-fab')) {",
        "  function startInterface() {\n    hkStartupStage = document.body ? 'BODY' : 'WAIT_BODY';\n    if (root?.isConnected && root.querySelector('#hk-fab')) {",
        'body stage')

    s=rep(s,
        "    try {\n      if (document.body) renderUI();",
        "    try {\n      if (document.body) { hkStartupStage = 'RENDER'; renderUI(); }",
        'render stage')

    s=rep(s,
        "    document.body.appendChild(root);\n    panel = root.querySelector('#hk-panel');",
        "    document.body.appendChild(root);\n    hkStartupStage = 'MOUNTED';\n    panel = root.querySelector('#hk-panel');",
        'mounted stage')

    s=rep(s,
        "    installFabDragging(permanentFab);\n    hideBootstrap();",
        "    installFabDragging(permanentFab);\n    hkStartupStage = 'FAB';\n    hideBootstrap();",
        'fab stage')

    anchor="    setInterval(updateWatermark, 30000);\n  }\n\n  function startNetworkCapture()"
    replacement="    setInterval(updateWatermark, 30000);\n    hkStartupStage = 'READY';\n  }\n\n  function startNetworkCapture()"
    s=rep(s,anchor,replacement,'ready stage')

    return validate(s)

def validate(s):
    for n in [
        MARKER,
        "let hkStartupStage = 'BOOT'",
        "bootstrapButton.textContent = problem ? 'HK!' : 'HK6'",
        "stage='+hkStartupStage",
        "hkStartupStage = document.body ? 'BODY' : 'WAIT_BODY'",
        "hkStartupStage = 'RENDER'",
        "hkStartupStage = 'MOUNTED'",
        "hkStartupStage = 'FAB'",
        "hkStartupStage = 'READY'",
        "HK_CORE_REVISION = 'core-20260920-r6'",
    ]: require(s,n,n)
    return s

if __name__=='__main__':
    s=TARGET.read_text(encoding='utf-8')
    TARGET.write_text(apply(s),encoding='utf-8')
    print('HK_STARTUP_STAGES_R7_OK')
