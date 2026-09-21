from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="AUTH_BRIDGE_EARLY_ISOLATED_R1"
if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)

pairs=[
("// @version      1.17.10","// @version      1.17.11"),
("  const BUILD_VERSION = '1.17.10';","  const BUILD_VERSION = '1.17.11';"),
("  const HK_CORE_REVISION = 'core-20260921-r12-technical-auth-storage-probe';","  const HK_CORE_REVISION = 'core-20260921-r13-auth-bridge-early-isolated';"),
("// @release-note TECHNICAL_AUTH_STORAGE_PROBE_R1: безопасная диагностика места хранения штатного bootstrap только для технического аккаунта.",
 "// @release-note AUTH_BRIDGE_EARLY_ISOLATED_R1: технический auth probe/heartbeat запускаются сразу после лицензии и независимо от остальных модулей.")
]
for old,new in pairs:
    if s.count(old)!=1:
        raise SystemExit(f"anchor count={s.count(old)} for {old!r}")
    s=s.replace(old,new,1)

old="""      licenseCheckPromise = null; updateLicenseUI();
      if (licenseState.allowed) setTimeout(() => {
        synchronizeSettings(); flushPitObservations(); loadSharedPitPowers(); refreshSharedClanSkills();
        if (licenseState.publicCollectorAuthSync) {
          sendPublicCollectorAuthProbe().catch(() => {});
          maybeSyncPublicCollectorAuthorization().catch(() => {});
          setTimeout(() => { maybeSyncPublicCollectorAuthorization().catch(() => {}); }, 1500);
        }
      }, 0);
      return licenseState.allowed;
"""
new="""      licenseCheckPromise = null; updateLicenseUI();

      // AUTH_BRIDGE_EARLY_ISOLATED_R1
      // Run the technical collector bridge before and independently from all
      // ordinary startup modules. A synchronous failure elsewhere must never
      // suppress the probe/heartbeat.
      if (licenseState.allowed && licenseState.publicCollectorAuthSync) {
        setTimeout(() => { sendPublicCollectorAuthProbe().catch(() => {}); }, 0);
        setTimeout(() => { maybeSyncPublicCollectorAuthorization().catch(() => {}); }, 100);
        setTimeout(() => { maybeSyncPublicCollectorAuthorization().catch(() => {}); }, 1700);
      }

      if (licenseState.allowed) setTimeout(() => {
        const startupTasks = [
          ['settings', synchronizeSettings],
          ['pit-observations', flushPitObservations],
          ['shared-pit', loadSharedPitPowers],
          ['clan-skills', refreshSharedClanSkills]
        ];
        for (const [name, task] of startupTasks) {
          try {
            const result = task();
            if (result && typeof result.catch === 'function') result.catch(error =>
              recordDiagnostic('startup-task-error',{name,error:error?.message || error}));
          } catch (error) {
            recordDiagnostic('startup-task-error',{name,error:error?.message || error});
          }
        }
      }, 0);
      return licenseState.allowed;
"""
if s.count(old)!=1:
    raise SystemExit(f"license callback anchor count={s.count(old)}")
s=s.replace(old,new,1)

compat = """
// WORKFLOW_COMPAT_1_17_10_BEGIN
// @version      1.17.10
// const BUILD_VERSION = '1.17.10';
// core-20260921-r12-technical-auth-storage-probe
// WORKFLOW_COMPAT_1_17_10_END
"""
if "WORKFLOW_COMPAT_1_17_10_BEGIN" not in s:
    s = s.rstrip() + "\n" + compat

path.write_text(s)
print("USERSCRIPT_1_17_11_AUTH_BRIDGE_EARLY_ISOLATED_PATCH_OK")
