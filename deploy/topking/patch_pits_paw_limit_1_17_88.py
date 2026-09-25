from pathlib import Path
import sys
import re

target = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/HamsterKingMobile.user.js")
s = target.read_text(encoding="utf-8")

def need(old, label, count=1):
    actual = s.count(old)
    if actual != count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")

def replace(old, new, label, count=1):
    global s
    need(old, label, count)
    s = s.replace(old, new, count)

replace(
    "// @version      1.17.87",
    "// @version      1.17.88\n"
    "// @release-note Ямы: удалён искусственный защитный лимит количества боёв. Яма продолжает бой, пока позволяет фактический запас Лап восстановления и выбранный лимит Лап; отдельного лимита на число боёв больше нет.",
    "metadata version",
)
replace(
    "const BUILD_VERSION = '1.17.87';",
    "const BUILD_VERSION = '1.17.88';",
    "build version",
)

marker = "const HK_PITS_CANON_REV = 'pits-canon-core-20260920-r1';"
if marker in s and "pits-paw-limited-battles-20260925-r1" not in s:
    s = s.replace(
        marker,
        marker + "\n  const HK_PITS_PAW_LIMIT_REV = 'pits-paw-limited-battles-20260925-r1';",
        1,
    )
elif "pits-paw-limited-battles-20260925-r1" not in s:
    # Keep the marker close to other Pits constants if the canonical revision
    # marker was renamed in a later patch.
    anchor = "const HK_PIT_RESTORATION_ITEM_ID = 'item_pit_health_ticket';"
    need(anchor, "Pits restoration item anchor")
    s = s.replace(
        anchor,
        anchor + "\n  const HK_PITS_PAW_LIMIT_REV = 'pits-paw-limited-battles-20260925-r1';",
        1,
    )

guard_patterns = [
    r"if\s*\(\s*\+\+battles\s*>\s*1000\s*\)\s*throw\s+new\s+Error\s*\(\s*`\$\{pitCanonDefinitionName\(def\)\}:\s*\$\{either\('защитный лимит боёв','battle safety limit'\)\}`\s*\)\s*;",
    r"if\s*\(\s*\+\+battles\s*>\s*1000\s*\)\s*throw\s+new\s+Error\([^\n;]*защитный лимит боёв[^\n;]*\);",
]
guard_count = 0
for pattern in guard_patterns:
    s, count = re.subn(pattern, "", s, count=1)
    guard_count += count
    if count:
        break
if guard_count != 1:
    pos = s.find("защитный лимит боёв")
    if pos >= 0:
        print("PITS_BATTLE_LIMIT_CONTEXT_BEGIN")
        print(s[max(0,pos-900):pos+1400])
        print("PITS_BATTLE_LIMIT_CONTEXT_END")
    raise SystemExit(f"Pits artificial battle limit: expected 1 replacement, got {guard_count}")

# Remove the now-unused local counter if present, without depending on its exact formatting.
s = re.sub(r"let\s+restorationSpent\s*=\s*0\s*,\s*battles\s*=\s*0\s*;", "let restorationSpent=0;", s, count=1)
s = re.sub(r"\s*let\s+battles\s*=\s*0\s*;", "", s, count=1)

for marker in [
    "// @version      1.17.88",
    "const BUILD_VERSION = '1.17.88';",
    "pits-paw-limited-battles-20260925-r1",
    "остановка по лимиту Лап восстановления",
]:
    if marker not in s:
        raise SystemExit("missing marker: " + marker)

for forbidden in [
    "battles>1000",
    "защитный лимит боёв",
    "battle safety limit",
]:
    if forbidden in s:
        raise SystemExit("artificial Pits battle limit still present: " + forbidden)

target.write_text(s, encoding="utf-8")
print("PITS_PAW_LIMIT_1_17_88=PASS")
print("version=1.17.88")
