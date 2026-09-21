from pathlib import Path
import runpy

# Transitional deploy wrapper: current race-safe workflow still invokes this
# legacy entrypoint. Delegate to the current 1.17.12 patch.
target = Path(__file__).with_name("patch_userscript_auth_bridge_xhr_1_17_12.py")
runpy.run_path(str(target), run_name="__main__")
