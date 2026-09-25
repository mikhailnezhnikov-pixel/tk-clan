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

# Version + release note.
replace(
    "// @version      1.17.86",
    "// @version      1.17.87\n"
    "// @release-note Ярмарка: Runner приведён к канону панели — текущие проходы и действия показываются в самом Runner, счётчик прогресса виден рядом со статусом, кнопки компактные; в общий журнал пишется итог запуска, а не поток проходов.",
    "metadata version",
)
replace(
    "const BUILD_VERSION = '1.17.86';",
    "const BUILD_VERSION = '1.17.87';",
    "build version",
)

marker_anchor = "const HK_FAIR_BONUS_SELECTION_REV = 'fair-bonus-selection-20260925-r1';"
replace(
    marker_anchor,
    marker_anchor + "\n  const HK_FAIR_RUNNER_CANON_REV = 'fair-runner-canon-20260925-r1';",
    "fair runner marker",
)

# Canonical Fair runner detection.
runner_decl_anchor = ",resourcesRun=visibleState&&Object.keys(RESOURCE_BUILDING_TYPES).some(kind=>title===resourceTypeName(kind)),businessesRun="
replace(
    runner_decl_anchor,
    ",resourcesRun=visibleState&&Object.keys(RESOURCE_BUILDING_TYPES).some(kind=>title===resourceTypeName(kind)),fairRun=visibleState&&title===either('Ярмарка','Fair'),businessesRun=",
    "runner Fair detection",
)

replace(
    "box.classList.toggle('resources-run',resourcesRun);",
    "box.classList.toggle('resources-run',resourcesRun);\n    box.classList.toggle('fair-run',fairRun);",
    "runner Fair class",
)

replace(
    "(buildingsRun||resourcesRun||exploreRun||businessesRun||hamstersRun||generalsRun)&&state.total",
    "(buildingsRun||resourcesRun||fairRun||exploreRun||businessesRun||hamstersRun||generalsRun)&&state.total",
    "runner Fair counter",
)

# Keep newest Fair pass visible in the Runner history.
history_anchor = "history.style.display=rows.length?'grid':'none';"
replace(
    history_anchor,
    "history.style.display=rows.length?'grid':'none';\n      if(fairRun&&rows.length) history.scrollTop=history.scrollHeight;",
    "runner Fair history autoscroll",
)

# Fair gets the same compact visual canon as the other production runners.
css_anchor = ".hk-runner.resources-run .hk-runner-history{border-color:#304057;background:#0c131d}"
fair_css = (
    css_anchor +
    ".hk-runner.fair-run{margin:0 0 14px;padding:14px 16px;border:1px solid #304057;border-radius:16px;background:#111925;box-shadow:none}"
    ".hk-runner.fair-run .hk-runner-head b{font-size:15px;color:#f2f5fa}"
    ".hk-runner.fair-run .hk-runner-state{padding:4px 8px;border-radius:999px;background:#1d2a3c;color:#cbd7e6;font-size:9px;font-weight:800}"
    ".hk-runner.fair-run .hk-runner-step{margin-top:7px;color:#9fb0c6;font-size:11px}"
    ".hk-runner.fair-run .hk-runner-track{height:7px;margin:10px 0 9px;background:#26364b}"
    ".hk-runner.fair-run .hk-runner-history{border-color:#304057;background:#0c131d}"
    ".hk-runner.fair-run .hk-runner-actions{justify-content:flex-end}"
    ".hk-runner.fair-run .hk-runner-actions button{flex:0 0 auto;width:auto;min-width:132px;min-height:36px;padding:9px 16px}"
)
replace(css_anchor, fair_css, "Fair runner compact CSS")

# Runner-only detail channel for Fair passes.
run_sig = "  async function runFair() {"
helper = "  function fairRunnerNote(message,type='') { hkRunner.note(message,type); }\n\n"
if helper.strip() not in s:
    need(run_sig, "runFair signature")
    s = s.replace(run_sig, helper + run_sig, 1)

# Route live pass-by-pass details to Runner history, not the global journal.
start = s.find(run_sig)
end = s.find("\n  function ordinaryShopGroup(", start)
if start < 0 or end < 0:
    raise SystemExit("runFair slice not found")
block = s[start:end]
detail_anchor = "    fairRunning = true; fairStop = false; updateFairControls();"
summary_anchor = "      if (bought >= buyLimit) {"
detail_pos = block.find(detail_anchor)
summary_pos = block.find(summary_anchor)
if detail_pos < 0 or summary_pos < 0 or summary_pos <= detail_pos:
    raise SystemExit("Fair detail/summary anchors not found")
prefix = block[:detail_pos + len(detail_anchor)]
details = block[detail_pos + len(detail_anchor):summary_pos]
summary = block[summary_pos:]
if "log(" not in details:
    raise SystemExit("No Fair pass logs found to reroute")
details = details.replace("log(", "fairRunnerNote(")
block = prefix + details + summary

# Manual stop / crash must leave a real result in the global journal.
old_abort = """      if (error?.name === 'AbortError') { hkRunner.reset(); log(either('Ярмарка остановлена','Fair stopped'),'warn'); }
      else { hkRunner.fail(error); log(`Аварийная остановка ярмарки: ${error.message}`, 'bad'); }"""
new_abort = """      if (error?.name === 'AbortError') {
        hkRunner.reset();
        log(either(
          `Ярмарка остановлена. Итог: основных покупок ${bought}/${buyLimit}, бонусных ${bonusBought}, прокруток ${rerolls}`,
          `Fair stopped. Result: main purchases ${bought}/${buyLimit}, bonus purchases ${bonusBought}, rerolls ${rerolls}`
        ),'warn');
      } else {
        hkRunner.fail(error);
        log(either(
          `Аварийная остановка Ярмарки: ${error?.message || error}. Итог: основных покупок ${bought}/${buyLimit}, бонусных ${bonusBought}, прокруток ${rerolls}`,
          `Fair failed: ${error?.message || error}. Result: main purchases ${bought}/${buyLimit}, bonus purchases ${bonusBought}, rerolls ${rerolls}`
        ),'bad');
      }"""
if old_abort not in block:
    raise SystemExit("Fair abort/failure summary anchor not found")
block = block.replace(old_abort, new_abort, 1)

s = s[:start] + block + s[end:]

# Static guards.
for marker in [
    "// @version      1.17.87",
    "const BUILD_VERSION = '1.17.87';",
    "fair-runner-canon-20260925-r1",
    "fairRun=visibleState&&title===either('Ярмарка','Fair')",
    "box.classList.toggle('fair-run',fairRun)",
    ".hk-runner.fair-run",
    "function fairRunnerNote(message,type='')",
    "fairRunnerNote(",
    "Ярмарка остановлена. Итог:",
]:
    if marker not in s:
        raise SystemExit("missing marker: " + marker)

# Global journal must still receive final success / early-stop summaries.
for final_marker in [
    "Цель Ярмарки достигнута: основных покупок",
    "Итог: основных покупок",
]:
    if final_marker not in block:
        raise SystemExit("missing Fair final journal summary: " + final_marker)

target.write_text(s, encoding="utf-8")
print("FAIR_RUNNER_CANON_1_17_87=PASS")
print("version=1.17.87")
