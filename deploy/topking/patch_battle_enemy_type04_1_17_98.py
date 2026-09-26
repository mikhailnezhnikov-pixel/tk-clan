from pathlib import Path
import sys

target=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=target.read_text(encoding="utf-8")

def need(old,label,count=1):
    actual=s.count(old)
    if actual!=count:
        raise SystemExit(f"{label}: expected {count}, got {actual}")

def rep(old,new,label,count=1):
    global s
    need(old,label,count)
    s=s.replace(old,new,count)

rep(
    "// @version      1.17.97",
    "// @version      1.17.98\n"
    "// @release-note Сражение: новый золотой враг type_04 (Хранитель Сокровищ) теперь учитывается решателем как полноценный противник с его HP и попадает в расчёт порядка атак.",
    "version"
)
rep("const BUILD_VERSION = '1.17.97';","const BUILD_VERSION = '1.17.98';","build")

anchor="  const HK_PUZZLE_SOLVER_REV = 'puzzle-solver-v3-embedded-20260921-r1';"
rep(
    anchor,
    "  const HK_PUZZLE_SOLVER_REV = 'puzzle-solver-v3-embedded-20260921-r1';\n"
    "  const HK_BATTLE_ENEMY_TYPE04_REV = 'battle-enemy-type04-20260926-r1';",
    "battle type04 marker"
)

rep(
    "        const match = id.match(/enemy_type_(01|02|03)_(\\d+)_sl(\\d+)/);",
    "        const match = id.match(/enemy_type_(01|02|03|04)_(\\d+)_sl(\\d+)/);",
    "battle enemy parser"
)

for marker in [
    "// @version      1.17.98",
    "const BUILD_VERSION = '1.17.98';",
    "battle-enemy-type04-20260926-r1",
    "enemy_type_(01|02|03|04)",
    "late-login-recovery-20260926-r1",
    "game-api-429-cooldown-20s-20260925-r1",
    "resource-maximum-direct-run-20260925-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

if "enemy_type_(01|02|03)_(\\d+)_sl(\\d+)" in s:
    raise SystemExit("old battle enemy parser still present")

target.write_text(s,encoding="utf-8")
print("BATTLE_ENEMY_TYPE04_1_17_98=PASS")
