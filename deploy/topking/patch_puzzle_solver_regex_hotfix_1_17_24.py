from pathlib import Path

PATH = Path("/tmp/HamsterKingMobile.user.js")
s = PATH.read_text(encoding="utf-8")
bs = chr(92)

replacements = [
    (
        "/mf_fairlot_lights_out_sl(d+)_(true|false)/",
        "/mf_fairlot_lights_out_sl(" + bs + "d+)_(true|false)/",
        "lights slot regex",
    ),
    (
        "/mf_treasurelot_sword_d+_(d+)/",
        "/mf_treasurelot_sword_" + bs + "d+_(" + bs + "d+)/",
        "battle sword regex",
    ),
    (
        "/enemy_type_(01|02|03)_(d+)_sl(d+)/",
        "/enemy_type_(01|02|03)_(" + bs + "d+)_sl(" + bs + "d+)/",
        "battle enemy regex",
    ),
]

for old, new, label in replacements:
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 broken marker, got {count}")
    s = s.replace(old, new, 1)

for broken in [
    "/mf_fairlot_lights_out_sl(d+)_(true|false)/",
    "/mf_treasurelot_sword_d+_(d+)/",
    "/enemy_type_(01|02|03)_(d+)_sl(d+)/",
]:
    if broken in s:
        raise SystemExit("broken puzzle regex still present: " + broken)

for marker in [
    "puzzle-solver-v3-embedded-20260921-r1",
    "/mf_fairlot_lights_out_sl(" + bs + "d+)_(true|false)/",
    "/mf_treasurelot_sword_" + bs + "d+_(" + bs + "d+)/",
    "/enemy_type_(01|02|03)_(" + bs + "d+)_sl(" + bs + "d+)/",
    "setInterval(checkPuzzle,500)",
    "setTimeout(checkPuzzle,300)",
]:
    if marker not in s:
        raise SystemExit("fixed marker missing: " + marker)

PATH.write_text(s, encoding="utf-8")
print("PUZZLE_SOLVER_REGEX_HOTFIX=PASS")
