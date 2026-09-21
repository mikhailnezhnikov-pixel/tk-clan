from pathlib import Path
import runpy

# Transitional deploy wrapper: the established race-safe workflow invokes this
# legacy entrypoint. Keep the live build at 1.17.12 and remove only the retired
# diagnostic auth-probe; auth-sync and passive login safety remain intact.
target = Path(__file__).with_name("patch_remove_public_collector_auth_probe_userscript.py")
runpy.run_path(str(target), run_name="__main__")
