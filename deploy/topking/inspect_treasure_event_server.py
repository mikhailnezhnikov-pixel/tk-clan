from pathlib import Path
import re

p=Path("/opt/hamsterking-license/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")
head=s[:18000]

def line(prefix):
    for row in head.splitlines():
        if row.startswith(prefix):
            return row
    return ""

print("LIVE_SCRIPT_VERSION",line("// @version"))
print("LIVE_UPDATE_URL",line("// @updateURL"))
print("LIVE_DOWNLOAD_URL",line("// @downloadURL"))
print("LIVE_BUILD_VERSION",re.search(r"const BUILD_VERSION = '([^']+)'",s).group(1) if re.search(r"const BUILD_VERSION = '([^']+)'",s) else "")
for marker in [
    "userscript-update-metadata-20260924-r1",
    "runtime-smoke-coverage-20260923-r1",
    "treasure-guide-bundle-card-dom-20260923-r1"
]:
    print("LIVE_MARKER",marker,marker in s)
