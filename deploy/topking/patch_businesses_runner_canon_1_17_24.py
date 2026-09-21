from pathlib import Path

PATH = Path("/tmp/HamsterKingMobile.user.js")
s = PATH.read_text(encoding="utf-8")

def replace_once(old, new, label):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 match, got {count}")
    s = s.replace(old, new, 1)

required = [
    "// @version      1.17.24",
    "const BUILD_VERSION = '1.17.24';",
    "const HK_CORE_REVISION = 'core-20260921-r26-businesses-rearrange-guard';",
    "const HK_BUSINESSES_REARRANGE_REV='businesses-rearrange-desktop-safe-t123-20260921-r1';",
    "function renderRunnerState()",
    "hkRunner.start({title:either('Перестановка бизнесов','Business rearrangement')",
    ".hk-runner.buildings-run{",
]
for marker in required:
    if marker not in s:
        raise SystemExit("missing expected marker: " + marker)

replace_once(
    "const HK_CORE_REVISION = 'core-20260921-r26-businesses-rearrange-guard';",
    "const HK_CORE_REVISION = 'core-20260921-r27-businesses-runner-canon';",
    "core revision"
)

replace_once(
    "const HK_BUSINESSES_REARRANGE_REV='businesses-rearrange-desktop-safe-t123-20260921-r1';",
    "const HK_BUSINESSES_REARRANGE_REV='businesses-rearrange-desktop-safe-t123-20260921-r1';\n  const HK_BUSINESSES_RUNNER_UI_REV='businesses-runner-canon-20260921-r1';",
    "business runner marker"
)

old_state = """    const visibleState=state.status!=='idle',title=String(state.title||''),exploreRun=visibleState&&[either('Исследование · E3','Explore · E3'),either('Исследование','Explore')].includes(title),buildingsRun=visibleState&&title===either('Здания','Buildings'); box.classList.toggle('show',visibleState);
    box.classList.toggle('pit-run',visibleState&&title===either('Ямы','Pits'));
    box.classList.toggle('explore-run',exploreRun);
    box.classList.toggle('buildings-run',buildingsRun);"""
new_state = """    const visibleState=state.status!=='idle',title=String(state.title||''),exploreRun=visibleState&&[either('Исследование · E3','Explore · E3'),either('Исследование','Explore')].includes(title),buildingsRun=visibleState&&title===either('Здания','Buildings'),businessesRun=visibleState&&title===either('Перестановка бизнесов','Business rearrangement'); box.classList.toggle('show',visibleState);
    box.classList.toggle('pit-run',visibleState&&title===either('Ямы','Pits'));
    box.classList.toggle('explore-run',exploreRun);
    box.classList.toggle('buildings-run',buildingsRun);
    box.classList.toggle('businesses-run',businessesRun);"""
replace_once(old_state,new_state,"runner mode detection")

replace_once(
    "root.querySelector('#hk-runner-state').textContent=(buildingsRun||exploreRun)&&state.total?`${stateLabel} · ${state.done}/${state.total}`:stateLabel;",
    "root.querySelector('#hk-runner-state').textContent=(buildingsRun||exploreRun||businessesRun)&&state.total?`${stateLabel} · ${state.done}/${state.total}`:stateLabel;",
    "runner state counter"
)

canon_css = """.hk-runner.businesses-run{margin:0 0 14px;padding:14px 16px;border:1px solid #304057;border-radius:16px;background:#111925;box-shadow:none}.hk-runner.businesses-run .hk-runner-head b{font-size:15px;color:#f2f5fa}.hk-runner.businesses-run .hk-runner-state{padding:4px 8px;border-radius:999px;background:#1d2a3c;color:#cbd7e6;font-size:9px;font-weight:800}.hk-runner.businesses-run .hk-runner-step{margin-top:7px;color:#9fb0c6;font-size:11px}.hk-runner.businesses-run .hk-runner-track{height:7px;margin:10px 0 9px;background:#26364b}.hk-runner.businesses-run .hk-runner-actions{justify-content:flex-end}.hk-runner.businesses-run .hk-runner-actions button{flex:0 0 auto;width:auto;min-width:132px;min-height:36px;padding:9px 16px}.hk-runner.businesses-run .hk-runner-history{border-color:#304057;background:#0c131d}"""
anchor = ".hk-runner.buildings-run .hk-runner-history{border-color:#304057;background:#0c131d}"
replace_once(anchor, anchor + canon_css, "business runner canonical css")

mobile_old = ".hk-runner.buildings-run .hk-runner-actions{display:grid;grid-template-columns:1fr 1fr}.hk-runner.buildings-run .hk-runner-actions button{width:100%;min-width:0}"
mobile_new = ".hk-runner.buildings-run .hk-runner-actions,.hk-runner.businesses-run .hk-runner-actions{display:grid;grid-template-columns:1fr 1fr}.hk-runner.buildings-run .hk-runner-actions button,.hk-runner.businesses-run .hk-runner-actions button{width:100%;min-width:0}"
if mobile_old in s:
    replace_once(mobile_old,mobile_new,"mobile runner canon")
else:
    # The mobile Buildings canon must exist in this baseline; fail rather than inventing another breakpoint.
    raise SystemExit("mobile buildings runner canon marker not found")

for marker in [
    "const HK_CORE_REVISION = 'core-20260921-r27-businesses-runner-canon';",
    "const HK_BUSINESSES_RUNNER_UI_REV='businesses-runner-canon-20260921-r1';",
    "box.classList.toggle('businesses-run',businessesRun);",
    "(buildingsRun||exploreRun||businessesRun)&&state.total",
    ".hk-runner.businesses-run{margin:0 0 14px;padding:14px 16px",
    ".hk-runner.businesses-run .hk-runner-actions{justify-content:flex-end}",
    ".hk-runner.buildings-run .hk-runner-actions,.hk-runner.businesses-run .hk-runner-actions{display:grid",
    "businesses-rearrange-desktop-safe-t123-20260921-r1",
    "businesses-catalog-readonly-20260921-r1",
    "explore-production-ui-20260921-r1",
    "buildings-native-sync-20260921-r1",
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: " + marker)

PATH.write_text(s, encoding="utf-8")
print("BUSINESSES_RUNNER_CANON_R1_PATCH=PASS")
