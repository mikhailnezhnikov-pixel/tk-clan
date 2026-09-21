from pathlib import Path
import runpy

# Transitional deploy wrapper: current race-safe workflow still invokes the
# 1.17.10 patch path. Delegate to the real 1.17.11 patch so we can publish the
# corrected client without changing the workflow transport itself.
target = Path(__file__).with_name("patch_userscript_auth_bridge_early_1_17_11.py")
runpy.run_path(str(target), run_name="__main__")
