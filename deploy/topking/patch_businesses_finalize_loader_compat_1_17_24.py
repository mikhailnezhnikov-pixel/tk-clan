from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")

old="const HK_CORE_REVISION = 'core-20260921-r28-businesses-finalize';"
new="const HK_CORE_REVISION = 'core-20260921-r27-businesses-runner-canon';"
if s.count(old)!=1:
    raise SystemExit(f"expected one r28 core marker, got {s.count(old)}")
for marker in [
    "// @version      1.17.24",
    "const HK_BUSINESSES_FINALIZE_REV='businesses-finalize-single-snapshot-20260921-r1';",
    "hkAuthoritativePlayerRead('business-final-check')",
    "let processedInsertRows = 0;",
    "businessesTitle?6000:1800",
    "function businessRemovalAllowed(",
    "businesses-runner-canon-20260921-r1",
]:
    if marker not in s:
        raise SystemExit("missing finalization marker: "+marker)
s=s.replace(old,new,1)
PATH.write_text(s,encoding="utf-8")
print("BUSINESSES_FINALIZE_LOADER_COMPAT_R1=PASS")
