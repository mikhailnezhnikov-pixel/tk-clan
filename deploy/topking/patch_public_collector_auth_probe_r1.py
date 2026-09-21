from pathlib import Path
import runpy

# The established race-safe workflow keeps this legacy path. The diagnostic
# auth-probe is retired; delegate to the removal patch while retaining auth-sync.
target = Path(__file__).with_name("patch_remove_public_collector_auth_probe_server.py")
runpy.run_path(str(target), run_name="__main__")
