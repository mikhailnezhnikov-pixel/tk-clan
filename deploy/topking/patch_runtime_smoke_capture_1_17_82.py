from pathlib import Path

path=Path('/tmp/HamsterKingMobile.user.js')
s=path.read_text(encoding='utf-8')

def replace_once(old,new,label):
    global s
    count=s.count(old)
    if count!=1:
        raise SystemExit(f'{label}: expected 1 match, got {count}')
    s=s.replace(old,new,1)

replace_once(
    "// @version      1.17.81\n",
    "// @version      1.17.82\n// @release-note Smoke-test: уже записанные обезличенные Rat Hunt / War / Районы evidence пассивно синхронизируются с HK backend; дополнительных запросов к игре нет.\n",
    'metadata version'
)
replace_once("const BUILD_VERSION = '1.17.81';","const BUILD_VERSION = '1.17.82';",'build version')

replace_once(
    "  const HK_RUNTIME_SMOKE_COVERAGE_REV = 'runtime-smoke-coverage-20260923-r1';\n",
    "  const HK_RUNTIME_SMOKE_COVERAGE_REV = 'runtime-smoke-coverage-20260923-r1';\n"
    "  const HK_RUNTIME_SMOKE_CAPTURE_REV = 'runtime-smoke-capture-20260924-r1';\n"
    "  let runtimeSmokeSyncTimer=null;\n"
    "  let runtimeSmokeLastFingerprint='';\n",
    'runtime smoke capture marker'
)

replace_once(
    "    if(event.type.startsWith('runtime-smoke-'))try{renderRuntimeSmokeStatus();}catch(_){}\n",
    "    if(event.type.startsWith('runtime-smoke-')){\n"
    "      try{renderRuntimeSmokeStatus();}catch(_){}\n"
    "      try{runtimeSmokeScheduleSync();}catch(_){}\n"
    "    }\n",
    'record diagnostic smoke sync'
)

anchor="  function renderRuntimeSmokeStatus() {\n"
helpers=r'''  function runtimeSmokeCaptureRows() {
    return diagnostic.events
      .filter(row=>String(row?.type||'').startsWith('runtime-smoke-'))
      .slice(-160);
  }

  function runtimeSmokeCaptureFingerprint(events,summary) {
    try{return diagnosticFingerprint(JSON.stringify({version:BUILD_VERSION,summary,events}));}
    catch(_){return diagnosticFingerprint(String(events?.length||0)+':'+BUILD_VERSION);}
  }

  async function runtimeSmokeSubmitSnapshot() {
    runtimeSmokeSyncTimer=null;
    if(!licenseState.allowed)return;
    const events=runtimeSmokeCaptureRows();
    if(!events.length)return;
    const summary=runtimeSmokeSummary();
    const fingerprint=runtimeSmokeCaptureFingerprint(events,summary);
    if(fingerprint===runtimeSmokeLastFingerprint)return;
    try{
      const result=await licensedServerJson(
        CLAN_SHOP_FACT_API_BASE,
        '/runtime-smoke/capture',
        {
          capture_key:'runtime-smoke:'+BUILD_VERSION+':'+fingerprint,
          script_version:BUILD_VERSION,
          revision:HK_RUNTIME_SMOKE_CAPTURE_REV,
          summary,
          events
        },
        false,
        'runtime-smoke-capture'
      );
      runtimeSmokeLastFingerprint=fingerprint;
      recordDiagnostic('smoke-sync',{
        revision:HK_RUNTIME_SMOKE_CAPTURE_REV,
        events:events.length,
        accepted:Number(result?.events||0)
      });
    }catch(error){
      recordDiagnostic('smoke-sync-error',{
        revision:HK_RUNTIME_SMOKE_CAPTURE_REV,
        status:Number(error?.httpStatus||0),
        message:String(error?.message||error||'').slice(0,500)
      });
    }
  }

  function runtimeSmokeScheduleSync(delay=1400) {
    if(runtimeSmokeSyncTimer)clearTimeout(runtimeSmokeSyncTimer);
    runtimeSmokeSyncTimer=setTimeout(()=>{void runtimeSmokeSubmitSnapshot();},Math.max(250,Number(delay)||1400));
  }

'''
if anchor not in s:
    raise SystemExit('render runtime smoke anchor missing')
s=s.replace(anchor,helpers+anchor,1)

replace_once(
    "      licenseCheckPromise = null; updateLicenseUI();\n",
    "      licenseCheckPromise = null; updateLicenseUI();\n"
    "      if(licenseState.allowed)try{runtimeSmokeScheduleSync(900);}catch(_){}\n",
    'license sync hook'
)

for marker in [
    "// @version      1.17.82",
    "const BUILD_VERSION = '1.17.82';",
    "userscript-update-metadata-20260924-r1",
    "runtime-smoke-coverage-20260923-r1",
    "runtime-smoke-capture-20260924-r1",
    "treasure-guide-bundle-card-dom-20260923-r1",
    "'/runtime-smoke/capture'",
    "function runtimeSmokeSubmitSnapshot()",
    "function runtimeSmokeScheduleSync("
]:
    if marker not in s:
        raise SystemExit('missing marker: '+marker)

if s.count("function runtimeSmokeSubmitSnapshot()")!=1:
    raise SystemExit('runtime smoke submit function mismatch')
if s.count("'/runtime-smoke/capture'")!=1:
    raise SystemExit('runtime smoke endpoint mismatch')

path.write_text(s,encoding='utf-8')
print('PATCH_1_17_82_RUNTIME_SMOKE_CAPTURE=PASS')
