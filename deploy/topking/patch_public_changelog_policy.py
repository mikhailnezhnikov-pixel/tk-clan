#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_public_changelog_policy.py USERSCRIPT SERVER")

userscript = Path(sys.argv[1])
server = Path(sys.argv[2])

s = userscript.read_text()
if "// @version      1.17.12" not in s or "const BUILD_VERSION = '1.17.12';" not in s:
    raise SystemExit("expected live userscript 1.17.12")

header_end = s.find("// ==/UserScript==")
if header_end < 0:
    raise SystemExit("userscript header end not found")
header = s[:header_end]
body = s[header_end:]

header = re.sub(r"^//\s*@release-note\s+.*\n?", "", header, flags=re.MULTILINE)
notes = (
    "// @release-note Исправлена проверка авторизации после входа в игру.\n"
    "// @release-note Улучшена стабильность запуска скрипта после авторизации.\n"
)
version_line = "// @version      1.17.12\n"
if version_line not in header:
    raise SystemExit("version line anchor missing")
header = header.replace(version_line, version_line + notes, 1)
s = header + body

sha_ui = "${update.sha256 ? `<small>SHA-256: ${escapeHtml(String(update.sha256).slice(0,16))}…</small>` : ''}"
if sha_ui in s:
    s = s.replace(sha_ui, "", 1)
if "SHA-256:" in s:
    raise SystemExit("public SHA label still present in userscript")

userscript.write_text(s)

srv = server.read_text()
old = '"sha256": release_sha256() if available else ""}'
new = '"sha256": ""}'
if old in srv:
    if srv.count(old) != 1:
        raise SystemExit(f"unexpected sha256 manifest anchor count={srv.count(old)}")
    srv = srv.replace(old, new, 1)
elif new not in srv:
    raise SystemExit("server release manifest sha256 anchor not found")

server.write_text(srv)
print("PUBLIC_CHANGELOG_POLICY_PATCH=PASS")
