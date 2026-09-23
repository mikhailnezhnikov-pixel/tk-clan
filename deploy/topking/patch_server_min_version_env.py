from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text(encoding="utf-8")

old='MIN_SCRIPT_VERSION = "1.17.8"  # FORCE_SAFE_USERSCRIPT_1_17_8_R1'
new='MIN_SCRIPT_VERSION = os.environ.get("HK_MIN_SCRIPT_VERSION", "1.17.8").strip() or "1.17.8"  # ENV_DRIVEN_USERSCRIPT_MIN_R1'

count=s.count(old)
if count!=1:
    raise SystemExit(f"minimum-version anchor mismatch: {count}")

s=s.replace(old,new,1)

if s.count("ENV_DRIVEN_USERSCRIPT_MIN_R1")!=1:
    raise SystemExit("minimum-version marker mismatch")
if 'MIN_SCRIPT_VERSION = "1.2.0"' not in s:
    raise SystemExit("self-test minimum fixture unexpectedly missing")

path.write_text(s,encoding="utf-8")
print("PATCH_SERVER_MIN_VERSION_ENV=PASS")
