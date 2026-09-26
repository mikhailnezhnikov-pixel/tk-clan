from pathlib import Path
import sys

target=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=target.read_text(encoding="utf-8")

def need(old,label,count=1):
    actual=s.count(old)
    if actual!=count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")

def rep(old,new,label,count=1):
    global s
    need(old,label,count)
    s=s.replace(old,new,count)

rep(
    "// @version      1.17.96",
    "// @version      1.17.97\n"
    "// @release-note Запуск на Safari/iPhone: late-login handoff больше не выжигает лимит попыток во время 429 cooldown. После паузы HK автоматически пробует снова; /player/me bootstrap стал коротким one-shot, а диагностическая кнопка показывает актуальную стадию вместо застывшего BOOT.",
    "version"
)
rep("const BUILD_VERSION = '1.17.96';","const BUILD_VERSION = '1.17.97';","build")

anchor="  const HK_LATE_LOGIN_HANDOFF_REV = 'late-login-handoff-20260921-r1';"
rep(anchor,anchor+"\n  const HK_LATE_LOGIN_RECOVERY_REV = 'late-login-recovery-20260926-r1';","late recovery marker")

old_show="""  function showBootstrap(problem = '') {
    bootstrapProblem = String(problem || bootstrapProblem || ('HK '+HK_CORE_REVISION+' · '+hkStartupStage));
    if (!bootstrapButton) {
      bootstrapButton = document.createElement('button');
      bootstrapButton.id = 'hk-bootstrap-button';
      bootstrapButton.dataset.hkRevision = HK_CORE_REVISION;
      bootstrapButton.type = 'button';
      bootstrapButton.style.cssText = 'position:fixed;right:16px;bottom:90px;z-index:2147483647;border:0;border-radius:50%;width:58px;height:58px;background:#ff9f1c;color:#16110a;font:bold 20px Arial;box-shadow:0 8px 24px #0008';
      bootstrapButton.onclick = () => alert(bootstrapProblem+'\\nrev='+HK_CORE_REVISION+'\\nstage='+hkStartupStage);
    }
    bootstrapButton.textContent = problem ? 'HK!' : 'HK…';
    const host = document.documentElement || document.head;
    if (host && !bootstrapButton.isConnected) host.appendChild(bootstrapButton);
  }"""
new_show="""  function showBootstrap(problem = '') {
    if (problem) bootstrapProblem = String(problem);
    if (!bootstrapButton) {
      bootstrapButton = document.createElement('button');
      bootstrapButton.id = 'hk-bootstrap-button';
      bootstrapButton.dataset.hkRevision = HK_CORE_REVISION;
      bootstrapButton.type = 'button';
      bootstrapButton.style.cssText = 'position:fixed;right:16px;bottom:90px;z-index:2147483647;border:0;border-radius:50%;width:58px;height:58px;background:#ff9f1c;color:#16110a;font:bold 20px Arial;box-shadow:0 8px 24px #0008';
      bootstrapButton.onclick = () => alert((bootstrapProblem || ('HK '+HK_CORE_REVISION+' · '+hkStartupStage))+'\\nrev='+HK_CORE_REVISION+'\\nstage='+hkStartupStage);
    }
    bootstrapButton.textContent = bootstrapProblem ? 'HK!' : 'HK…';
    const host = document.documentElement || document.head;
    if (host && !bootstrapButton.isConnected) host.appendChild(bootstrapButton);
  }"""
rep(old_show,new_show,"dynamic bootstrap diagnostic")

rep(
    "      const documentValue = await apiJson('/player/me', 'POST', null, true, 2);",
    "      const documentValue = await apiJson('/player/me', 'POST', null, true, 0, 10000);",
    "late bootstrap one-shot"
)

old_try="""  async function hkTryLateLoginHandoff() {
    if (hkNativeGameLoginReady() || hkLateLoginHandoffBusy) return hkNativeGameLoginReady();
    if (Date.now() < hkLateLoginHandoffNextAt || hkLateLoginHandoffAttempts >= 6) return false;

    restoreGameApiBaseFromPerformance();
    refreshStoredGameAuthorization();
    const token = currentGameBearer();
    const tokenReady = !!token && jwtExpiration(token) > Date.now() + 5000;
    const nativePlayerMeSeen = hkPriorNativePlayerMeEvidence();
    const nativeAuthParams = readNativeGameAuthParams();
    const storageFallbackReady =
      Date.now() - hkLateLoginHandoffStartedAt >= 2500 &&
      !!nativeAuthParams?.authType &&
      !!nativeAuthParams?.authData &&
      tokenReady;

    // We never create a game session here. Late handoff is allowed only after
    // evidence that the native game has already authenticated, then performs
    // one read-only /player/me to recover state missed by a late bookmarklet.
    if (!tokenReady || (!nativePlayerMeSeen && !storageFallbackReady)) return false;

    hkLateLoginHandoffBusy = true;
    hkLateLoginHandoffAttempts += 1;
    hkLateLoginHandoffNextAt = Date.now() + 1500;
    hkStartupStage = 'LATE_HANDOFF';
    recordDiagnostic('late-login-handoff-attempt', {
      revision:HK_LATE_LOGIN_HANDOFF_REV,
      attempt:hkLateLoginHandoffAttempts,
      nativePlayerMeSeen,
      authSource:nativeAuthParams?.source || '',
      tokenFingerprint:diagnosticFingerprint(token),
    });
    try {
      const ok = await bootstrapLateGameConnection();
      recordDiagnostic('late-login-handoff-result', {ok, attempt:hkLateLoginHandoffAttempts});
      return !!ok && hkNativeGameLoginReady();
    } finally {
      hkLateLoginHandoffBusy = false;
      if (!hkNativeGameLoginReady()) hkStartupStage = 'WAIT_NATIVE_LOGIN';
    }
  }"""

new_try="""  async function hkTryLateLoginHandoff() {
    if (hkNativeGameLoginReady() || hkLateLoginHandoffBusy) return hkNativeGameLoginReady();
    const now=Date.now();
    if (now < hkLateLoginHandoffNextAt) return false;

    // A local 429 gate is not a failed login attempt. Do not burn through the
    // recovery loop while Game API is intentionally cooling down.
    const cooldown=Math.max(0,gameApiCooldownRemainingMs());
    if(cooldown>0){
      hkLateLoginHandoffNextAt=now+cooldown+250;
      hkStartupStage='WAIT_NATIVE_LOGIN';
      recordDiagnostic('late-login-handoff-cooldown',{revision:HK_LATE_LOGIN_RECOVERY_REV,cooldownMs:cooldown});
      return false;
    }

    restoreGameApiBaseFromPerformance();
    refreshStoredGameAuthorization();
    const token = currentGameBearer();
    const tokenReady = !!token && jwtExpiration(token) > Date.now() + 5000;
    const nativePlayerMeSeen = hkPriorNativePlayerMeEvidence();
    const nativeAuthParams = readNativeGameAuthParams();
    const storageFallbackReady =
      Date.now() - hkLateLoginHandoffStartedAt >= 2500 &&
      !!nativeAuthParams?.authType &&
      !!nativeAuthParams?.authData &&
      tokenReady;

    // We never create a game session here. Late handoff is allowed only after
    // evidence that the native game has already authenticated, then performs
    // one read-only /player/me to recover state missed by a late bookmarklet.
    if (!tokenReady || (!nativePlayerMeSeen && !storageFallbackReady)) return false;

    hkLateLoginHandoffBusy = true;
    hkLateLoginHandoffAttempts += 1;
    hkLateLoginHandoffNextAt = Date.now() + Math.min(8000,1500 + hkLateLoginHandoffAttempts*500);
    hkStartupStage = 'LATE_HANDOFF';
    bootstrapProblem='';
    showBootstrap();
    recordDiagnostic('late-login-handoff-attempt', {
      revision:HK_LATE_LOGIN_RECOVERY_REV,
      attempt:hkLateLoginHandoffAttempts,
      nativePlayerMeSeen,
      authSource:nativeAuthParams?.source || '',
      tokenFingerprint:diagnosticFingerprint(token),
    });
    try {
      const ok = await bootstrapLateGameConnection();
      const afterCooldown=Math.max(0,gameApiCooldownRemainingMs());
      if(!ok && afterCooldown>0) hkLateLoginHandoffNextAt=Date.now()+afterCooldown+250;
      recordDiagnostic('late-login-handoff-result', {ok, attempt:hkLateLoginHandoffAttempts, cooldownMs:afterCooldown});
      return !!ok && hkNativeGameLoginReady();
    } finally {
      hkLateLoginHandoffBusy = false;
      if (!hkNativeGameLoginReady()) hkStartupStage = 'WAIT_NATIVE_LOGIN';
    }
  }"""
rep(old_try,new_try,"late login recovery loop")

for marker in [
    "// @version      1.17.97",
    "const BUILD_VERSION = '1.17.97';",
    "late-login-recovery-20260926-r1",
    "gameApiCooldownRemainingMs()",
    "hkLateLoginHandoffNextAt=now+cooldown+250",
    "apiJson('/player/me', 'POST', null, true, 0, 10000)",
    "bootstrapProblem='';",
    "resource-maximum-direct-run-20260925-r1",
    "game-api-429-cooldown-20s-20260925-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

if "hkLateLoginHandoffAttempts >= 6" in s:
    raise SystemExit("old finite late-handoff attempt cap still present")
if "apiJson('/player/me', 'POST', null, true, 2)" in s:
    raise SystemExit("old retrying late-bootstrap player/me still present")

target.write_text(s,encoding="utf-8")
print("LATE_LOGIN_RECOVERY_1_17_97=PASS")
