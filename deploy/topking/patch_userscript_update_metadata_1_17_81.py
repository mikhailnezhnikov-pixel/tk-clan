from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")
MARKER="userscript-update-metadata-20260924-r1"
UPDATE_URL="https://hk-license.89.125.1.71.sslip.io/panel.js"

if MARKER in s:
    print("USERSCRIPT_UPDATE_METADATA_ALREADY_PRESENT")
    raise SystemExit(0)

for required in [
    "// @version      1.17.80",
    "const BUILD_VERSION = '1.17.80';",
    "// @match        https://app.hamsterking.games/*",
    "// @run-at       document-start",
    "// @grant        none",
    "runtime-smoke-coverage-20260923-r1",
    "treasure-guide-bundle-card-dom-20260923-r1",
]:
    if required not in s:
        raise SystemExit("missing marker: "+required)

s=s.replace("// @version      1.17.80","// @version      1.17.81",1)
s=s.replace("const BUILD_VERSION = '1.17.80';","const BUILD_VERSION = '1.17.81';",1)

pos=s.find("// @release-note ")
if pos>=0:
    s=s[:pos]+"// @release-note Обновление userscript: добавлены штатные update/download URL на текущий panel.js; после ручного перехода на эту версию менеджер userscript сможет проверять и загружать новые версии автоматически.\n"+s[pos:]

old="""// @match        https://app.hamsterking.games/*
 // @run-at       document-start
"""
if old in s:
    new=f"""// @match        https://app.hamsterking.games/*
 // @updateURL    {UPDATE_URL}
 // @downloadURL  {UPDATE_URL}
 // @run-at       document-start
"""
    s=s.replace(old,new,1)
else:
    old="""// @match        https://app.hamsterking.games/*
// @run-at       document-start
"""
    new=f"""// @match        https://app.hamsterking.games/*
// @updateURL    {UPDATE_URL}
// @downloadURL  {UPDATE_URL}
// @run-at       document-start
"""
    if old not in s:
        raise SystemExit("metadata anchor missing")
    s=s.replace(old,new,1)

anchor="  const BUILD_VERSION = '1.17.81';\n"
insert=anchor+"  const HK_USERSCRIPT_UPDATE_META_REV = 'userscript-update-metadata-20260924-r1';\n"
if anchor not in s:
    raise SystemExit("build version anchor missing")
s=s.replace(anchor,insert,1)

for marker in [
    "// @version      1.17.81",
    "const BUILD_VERSION = '1.17.81';",
    "HK_USERSCRIPT_UPDATE_META_REV = 'userscript-update-metadata-20260924-r1'",
    f"// @updateURL    {UPDATE_URL}",
    f"// @downloadURL  {UPDATE_URL}",
    "runtime-smoke-coverage-20260923-r1",
    "treasure-guide-bundle-card-dom-20260923-r1",
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

if s.count("// @updateURL") != 1 or s.count("// @downloadURL") != 1:
    raise SystemExit("update metadata count mismatch")

PATH.write_text(s,encoding="utf-8")
print("USERSCRIPT_UPDATE_METADATA_1_17_81=PASS")
