from pathlib import Path
import re, sys

path=Path("baseline/topking/HamsterKingMobile.current.user.js")
s=path.read_text(encoding="utf-8")
checks=[]

def check(name, cond, detail=""):
    checks.append((name, bool(cond), detail))
    if not cond:
        print("FAIL", name, detail)

def section(start_marker, next_markers=("\n  function ","\n  async function ","\n\n  // ")):
    i=s.find(start_marker)
    if i<0:
        return ""
    candidates=[]
    for marker in next_markers:
        j=s.find(marker,i+len(start_marker))
        if j>i:
            candidates.append(j)
    j=min(candidates) if candidates else len(s)
    return s[i:j]

rat=section("  async function runRatHuntCombat() {")
war=section("  async function runWarCombat() {")
neigh=section("  async function runNeighborhoodBattles() {")
neigh_post=section("  async function neighborhoodPost(path,body) {")
api_core=section("  async function apiJsonCore(")
runner=s[s.find("  const hkRunner = (() => {"):s.find("\n  // Optional bridge",s.find("  const hkRunner = (() => {"))]
server_json=section("  async function licensedServerJson(")
license_check=section("  async function checkLicense(player, force = false) {")

check("version_metadata", "// @version      1.17.83" in s)
check("version_build", "const BUILD_VERSION = '1.17.83';" in s)
check("update_url", "// @updateURL    https://hk-license.89.125.1.71.sslip.io/panel.js" in s)
check("download_url", "// @downloadURL  https://hk-license.89.125.1.71.sslip.io/panel.js" in s)
check("update_metadata_marker", "userscript-update-metadata-20260924-r1" in s)
check("server_health_scope_marker", "server-health-core-20260924-r1" in s)
for marker in [
    "stage7-combat-confirm-20260923-r1",
    "rat-hunt-combat-20260923-r1",
    "war-combat-20260923-r1",
    "neighborhood-battles-20260923-r1",
    "runtime-smoke-observability-20260923-r1",
    "runtime-smoke-session-20260923-r1",
    "runtime-smoke-fresh-run-20260923-r1",
    "runtime-smoke-autostart-20260923-r1",
    "runtime-smoke-coverage-20260923-r1",
]:
    check("marker:"+marker, marker in s)

check("runner_abort_controller", "new AbortController()" in runner and "abortController?.abort(reason)" in runner)
check("runner_pause_wait", "async waitIfPaused()" in runner and "while(state.status==='paused')" in runner)
check("runner_stop_settles_pause", "settlePaused();" in runner and "state.status='stopping'" in runner)

check("api_retry_zero_supported", "const maxRetries" in api_core and "Math.max(0, Math.trunc(Number(retryNetwork) || 0))" in api_core)
check("api_network_retry_guarded", "if (attempt < maxRetries)" in api_core)
check("api_5xx_retry_guarded", "const transient = response.status === 408 || response.status === 425 || response.status >= 500;" in api_core and "if (transient && attempt < maxRetries)" in api_core)
check("api_429_no_hidden_retry", "if (response.status === 429) throw gameApiRateLimitError(path,response);" in api_core)

check("rat_confirm", "if(!confirm(either(" in rat)
check("rat_smoke_clean_start", "runtimeSmokeResetModule('rat-hunt')" in rat and "hkRuntimeSmokeRecord('rat-hunt-start'" in rat)
check("rat_fresh_preflight", "hkAuthoritativePlayerRead('rat-hunt:preflight')" in rat)
for endpoint in [
    "/pit_generals/change_preset",
    "/pit_generals/start",
    "/pit_generals/pass",
    "/pit_generals/respawn",
    "/pit_generals/battle",
    "/pit_generals/finish",
]:
    idx=rat.find(endpoint)
    check("rat_mutation_retry0:"+endpoint, idx>=0 and "true,0" in rat[idx:idx+240])
check("rat_pause_abort", rat.count("hkRunner.waitIfPaused()")>=2 and "hkRunner.signal?.aborted" in rat)
check("rat_final_authoritative_refresh", "hkAuthoritativePlayerRead('rat-hunt:complete')" in rat)
check("rat_smoke_terminal", "hkRuntimeSmokeRecord('rat-hunt-complete'" in rat and "hkRuntimeSmokeRecord('rat-hunt-error'" in rat)

check("war_confirm", "if(!confirm(either(" in war)
check("war_smoke_clean_start", "runtimeSmokeResetModule('war')" in war and "hkRuntimeSmokeRecord('war-start'" in war)
check("war_fresh_preflight", "hkAuthoritativePlayerRead('wars:preflight')" in war)
check("war_active_refetch", "warFetchActiveBattles()" in war)
check("war_cost_refetch", "warFetchAttackCost()" in war)
check("war_opponents_refetch", "warFetchOpponents()" in war)
for endpoint in ["/alliance_war/buy_pass","/alliance_war/fight"]:
    idx=war.find(endpoint)
    check("war_mutation_retry0:"+endpoint, idx>=0 and "true,0" in war[idx:idx+260])
check("war_pause_abort", "hkRunner.waitIfPaused()" in war and "hkRunner.signal?.aborted" in war)
check("war_final_authoritative_refresh", "hkAuthoritativePlayerRead('wars:complete')" in war)
check("war_smoke_terminal", "hkRuntimeSmokeRecord('war-complete'" in war and "hkRuntimeSmokeRecord('war-error'" in war)

check("neigh_initial_fresh_view", "refreshNeighborhoodBattles(false)" in neigh)
check("neigh_confirm", "if(!confirm(either(" in neigh)
check("neigh_smoke_clean_start", "runtimeSmokeResetModule('neighborhood')" in neigh and "hkRuntimeSmokeRecord('neighborhood-start'" in neigh)
check("neigh_second_preflight_view", "apiJson('/idler/view','GET',null,true,1)" in neigh and "neighborhood:run-preflight" in neigh)
check("neigh_mutation_helper_retry0", "apiJson(path,'POST',body,true,0)" in neigh_post)
for endpoint in ["/idler/claim","/idler/update","/idler/level","/idler/tap"]:
    check("neigh_endpoint:"+endpoint, endpoint in neigh)
check("neigh_pause_abort", neigh.count("hkRunner.waitIfPaused()")>=3 and "hkRunner.signal?.aborted" in neigh)
check("neigh_409_recovery", "status===409" in neigh)
check("neigh_429_5xx_recovery", "status===429||status>=500||error?.name==='HKRateLimitError'" in neigh)
check("neigh_smoke_terminal", "hkRuntimeSmokeRecord('neighborhood-complete'" in neigh and "hkRuntimeSmokeRecord('neighborhood-error'" in neigh)

check("smoke_session_storage", "hk_runtime_smoke_events_v1" in s and "sessionStorage" in s)
check("smoke_module_reset", "function runtimeSmokeResetModule(" in s)
check("smoke_json_export", "function downloadRuntimeSmokeReport()" in s and "topking-hk-runtime-smoke-v1" in s)
check("smoke_coverage_3", "function runtimeSmokeCoverage(" in s and "total:3" in s)
check("smoke_no_auto_pass", "auto_runtime_pass" not in s.lower())
check("smoke_capture_marker", "runtime-smoke-capture-20260924-r1" in s)
check("smoke_capture_submit", "function runtimeSmokeSubmitSnapshot()" in s and "'/runtime-smoke/capture'" in s)
check("smoke_capture_debounce", "function runtimeSmokeScheduleSync(" in s and "runtimeSmokeSyncTimer" in s)
check("smoke_capture_license_guard", "if(!licenseState.allowed)return;" in section("  async function runtimeSmokeSubmitSnapshot() {"))
check("smoke_capture_events_only", "runtimeSmokeCaptureRows()" in s and "startsWith('runtime-smoke-')" in s)
check("smoke_capture_no_game_endpoint", "CLAN_SHOP_FACT_API_BASE" in section("  async function runtimeSmokeSubmitSnapshot() {"))
check("smoke_capture_on_license", "if(licenseState.allowed)try{runtimeSmokeScheduleSync(900);" in s)

check("server_health_writer_count", s.count("setHealth('server'") == 2)
check("server_health_core_authoritative", "setHealth('server', response.ok" in license_check)
check("server_health_core_network_failure", "setHealth('server', false, 'сервер недоступен')" in license_check)
check("server_health_optional_no_global_write", "setHealth('server'" not in server_json)
check("server_health_optional_diagnostic", server_json.count("server-endpoint-unavailable") >= 2)
check("server_health_manual_recheck", "await checkLicense(playerDocument.player || {}, true)" in s)


failed=[x for x in checks if not x[1]]
print("HK_1_17_83_FINAL_STATIC_GATE="+("PASS" if not failed else "FAIL"))
print("checks_total="+str(len(checks)))
print("checks_pass="+str(len(checks)-len(failed)))
print("checks_fail="+str(len(failed)))
for name,ok,detail in checks:
    print(("PASS" if ok else "FAIL")+" "+name+((" "+detail) if detail else ""))
if failed:
    sys.exit(1)
