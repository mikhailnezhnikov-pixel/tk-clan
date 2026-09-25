from pathlib import Path
import sys

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

replace(
    "      let restorationSpent=0,battles=0;",
    "      let restorationSpent=0;",
    "Pits artificial battle counter",
)

old_guard = """        await hkRunner.waitIfPaused();if(hkRunner.signal?.aborted)throw new DOMException('Aborted','AbortError');if(++battles>1000)throw new Error(`${pitCanonDefinitionName(def)}: ${either('защитный лимит боёв','battle safety limit')}`);"""
new_guard = """        await hkRunner.waitIfPaused();if(hkRunner.signal?.aborted)throw new DOMException('Aborted','AbortError');"""
replace(old_guard, new_guard, "Pits artificial battle limit")

for marker in [
    "// @version      1.17.88",
    "const BUILD_VERSION = '1.17.88';",
    "pits-paw-limited-battles-20260925-r1",
    "let restorationSpent=0;",
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
