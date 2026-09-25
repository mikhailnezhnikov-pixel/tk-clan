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

# Version and user-facing release note.
replace(
    "// @version      1.17.85",
    "// @version      1.17.86\n"
    "// @release-note Ярмарка: выбор бонусных лотов ×5/×10/×30 снова определяется выбранным максимумом групп 3/6/9, а не полем «Цель основных покупок». При 9 доступны все три флажка; фактический выкуп по-прежнему происходит только после открытия соответствующего порога.",
    "metadata version",
)
replace(
    "const BUILD_VERSION = '1.17.85';",
    "const BUILD_VERSION = '1.17.86';",
    "build version",
)

# Marker for the regression fix.
anchor = "const HK_FAIR_BONUS_COST_FORECAST_REV = 'fair-bonus-cost-forecast-20260923-r1';"
replace(
    anchor,
    anchor + "\n  const HK_FAIR_BONUS_SELECTION_REV = 'fair-bonus-selection-20260925-r1';",
    "fair bonus selection marker",
)

# Regression introduced in 1.17.63:
# checkbox availability was tied to the current main-purchase target.
# The 3/6/9 selector is the capability switch; the target only controls
# how many main purchases the current run attempts.
old_bonus = """  function availableFairBonusLots(exactLots = fairComboSettings().exactLots, buyLimit = fairBuyTargetValue(root?.querySelector('#hk-fair-buy-limit')?.value, exactLots)) {
    const reachable = Math.min(9, Math.max(0, exactLots), Math.max(0, buyLimit));
    return reachable >= 9 ? [5, 10, 30] : reachable >= 6 ? [5, 10] : reachable >= 3 ? [5] : [];
  }"""
new_bonus = """  function availableFairBonusLots(exactLots = fairComboSettings().exactLots) {
    const maximum = Math.max(0, Math.trunc(Number(exactLots || 0)));
    return maximum >= 9 ? [5, 10, 30] : maximum >= 6 ? [5, 10] : maximum >= 3 ? [5] : [];
  }"""
replace(old_bonus, new_bonus, "fair bonus availability function")

# Make intent explicit at the two known callers. Extra main-purchase target
# must not disable a checkbox; execution still checks which bonus slot is
# actually opened on the live board.
for old, new, label in [
    ("availableFairBonusLots(exactLots, buyLimit)", "availableFairBonusLots(exactLots)", "forecast availability call"),
    ("availableFairBonusLots(combo.exactLots, buyLimit)", "availableFairBonusLots(combo.exactLots)", "run availability call"),
]:
    actual = s.count(old)
    if actual:
        s = s.replace(old, new)
    elif new not in s:
        raise SystemExit(f"{label}: neither old nor new form found")

# Static regression guards.
for marker in [
    "// @version      1.17.86",
    "const BUILD_VERSION = '1.17.86';",
    "fair-bonus-selection-20260925-r1",
    "function availableFairBonusLots(exactLots = fairComboSettings().exactLots)",
    "return maximum >= 9 ? [5, 10, 30] : maximum >= 6 ? [5, 10] : maximum >= 3 ? [5] : [];",
]:
    if marker not in s:
        raise SystemExit("missing marker: " + marker)

if "const reachable = Math.min(9, Math.max(0, exactLots), Math.max(0, buyLimit));" in s:
    raise SystemExit("old buyLimit-gated bonus availability still present")

target.write_text(s, encoding="utf-8")
print("FAIR_BONUS_SELECTION_1_17_86=PASS")
print("version=1.17.86")
