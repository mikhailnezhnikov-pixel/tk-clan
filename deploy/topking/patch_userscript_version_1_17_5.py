from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
old_version="1.17.4"
new_version="1.17.5"

anchors=[
    ("// @version      "+old_version, "// @version      "+new_version),
    ("  const BUILD_VERSION = '"+old_version+"';", "  const BUILD_VERSION = '"+new_version+"';"),
]
for old,new in anchors:
    if s.count(old)!=1:
        raise SystemExit(f"version anchor count for {old!r}: {s.count(old)}")
    s=s.replace(old,new,1)

old_note="// @release-note Hotfix версии bookmarklet: metadata и runtime version синхронизированы; аудит валют и live-state сохранён."
new_note="// @release-note Автоматическое обновление авторизации серверного public collector для технического аккаунта; Maps и Explore без изменений."
if s.count(old_note)==1:
    s=s.replace(old_note,new_note,1)
else:
    lines=s.splitlines()
    for i,line in enumerate(lines):
        if line.startswith("// @release-note "):
            lines[i]=new_note
            s="\n".join(lines)+("\n" if s.endswith("\n") else "")
            break
    else:
        raise SystemExit("release-note anchor missing")

# Force takeover if 1.17.5 is installed while an older runtime is still present.
old_core="  const HK_CORE_REVISION = 'core-20260920-r6';"
new_core="  const HK_CORE_REVISION = 'core-20260921-r7-auth-heartbeat';"
if s.count(old_core)==1:
    s=s.replace(old_core,new_core,1)
elif new_core not in s:
    raise SystemExit("core revision anchor missing")

path.write_text(s)
print("VERSION_1_17_5_PATCH_OK")
