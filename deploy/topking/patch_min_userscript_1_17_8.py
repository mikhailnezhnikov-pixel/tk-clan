from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="FORCE_SAFE_USERSCRIPT_1_17_8_R1"
if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)

old='MIN_SCRIPT_VERSION = os.environ.get("HK_MIN_SCRIPT_VERSION", "1.2.0").strip() or "1.2.0"'
new='MIN_SCRIPT_VERSION = "1.17.8"  # FORCE_SAFE_USERSCRIPT_1_17_8_R1'
if s.count(old)!=1:
    raise SystemExit(f"minimum-version anchor count={s.count(old)}")
s=s.replace(old,new,1)

path.write_text(s)
print("FORCE_SAFE_USERSCRIPT_1_17_8_R1_PATCH_OK")
