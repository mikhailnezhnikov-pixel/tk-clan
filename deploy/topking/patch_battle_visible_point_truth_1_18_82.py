from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

def rep(old,new,label,count=1):
    global s
    n=s.count(old)
    if n!=count:
        raise SystemExit(f"{label}: expected {count} got {n}")
    s=s.replace(old,new,count)

rep(
    "// @version      1.18.81",
    "// @version      1.18.82\n"
    "// @release-note Сражение: убран ошибочный запрет на атаки нижних рядов на больших экранах. Если центр карточки врага реально видим и elementFromPoint подтверждает, что клик попадает именно в неё, атака разрешается независимо от процента высоты экрана. Прокрутка выполняется только когда цель вне viewport или реально перекрыта нижней панелью.",
    "version"
)
rep("const BUILD_VERSION = '1.18.81';","const BUILD_VERSION = '1.18.82';","build")

anchor="  const HK_BATTLE_TARGET_SCROLL_REV='battle-target-safe-scroll-20260928-r1';"
rep(
    anchor,
    anchor+"\n  const HK_BATTLE_VISIBLE_POINT_TRUTH_REV='battle-visible-point-truth-20260929-r1';",
    "visible point revision"
)

old_band=r'''    function battleTargetSafeBand(element) {
      const probe=battleElementTapProbe(element);
      if (!probe.ready) return false;
      const cy=probe.y;
      // Keep enemy cards away from the sticky game footer / Safari toolbar and
      // away from the top navigation. The middle of the visual viewport is the
      // only device-neutral click area shared by iPhone, tablet and desktop.
      const top=Math.max(90,window.innerHeight*0.24);
      const bottom=Math.min(window.innerHeight-140,window.innerHeight*0.68);
      return cy>=top && cy<=Math.max(top+40,bottom);
    }
'''
new_band=r'''    function battleTargetSafeBand(element) {
      // The real clickability test is elementFromPoint ownership, not an
      // arbitrary percentage of viewport height. On desktop and tall phones a
      // perfectly clickable last row can naturally sit below 68% of the screen.
      // If the game footer truly covers it, battleElementTapProbe() reports the
      // footer as the leaf and returns ready:false.
      const probe=battleElementTapProbe(element);
      return !!probe.ready;
    }
'''
rep(old_band,new_band,"remove fixed viewport band")

old_initial=r'''      if (!element || !element.isConnected) return false;
      if (battleTargetSafeBand(element)) return true;

      const before=element.getBoundingClientRect?.();
'''
new_initial=r'''      if (!element || !element.isConnected) return false;
      const initialProbe=battleElementTapProbe(element);
      if (initialProbe.ready) {
        recordDiagnostic('battle-target-already-clickable',{
          revision:HK_BATTLE_VISIBLE_POINT_TRUTH_REV,
          label,
          centerY:Math.round(initialProbe.y||0),
          viewportHeight:window.innerHeight
        });
        return true;
      }

      const before=element.getBoundingClientRect?.();
'''
rep(old_initial,new_initial,"initial probe truth")

old_mid=r'''      let probe=battleElementTapProbe(element);
      if (!probe.ready || !battleTargetSafeBand(element)) {
'''
new_mid=r'''      let probe=battleElementTapProbe(element);
      if (!probe.ready) {
'''
rep(old_mid,new_mid,"scroll only if actually blocked")

old_success=r'''      const success=probe.ready && battleTargetSafeBand(element);
'''
new_success=r'''      const success=!!probe.ready;
'''
rep(old_success,new_success,"success actual clickability")

old_runner=r'''        const targetProbe=battleElementTapProbe(element);
        if (!targetProbe.ready || !battleTargetSafeBand(element)) {
'''
new_runner=r'''        const targetProbe=battleElementTapProbe(element);
        if (!targetProbe.ready) {
'''
rep(old_runner,new_runner,"runner actual clickability")

rep(
    "reason:'target-not-safe-after-scroll',",
    "reason:'target-not-clickable-after-scroll',",
    "diagnostic reason"
)

export_anchor="      battleTargetScrollRevision:HK_BATTLE_TARGET_SCROLL_REV,"
rep(
    export_anchor,
    export_anchor+"\n      battleVisiblePointTruthRevision:HK_BATTLE_VISIBLE_POINT_TRUTH_REV,",
    "debug export"
)

for marker in [
    "// @version      1.18.82",
    "const BUILD_VERSION = '1.18.82';",
    "battle-visible-point-truth-20260929-r1",
    "return !!probe.ready;",
    "if (initialProbe.ready)",
    "if (!probe.ready) {",
    "const success=!!probe.ready;",
    "reason:'target-not-clickable-after-scroll'",
    "battleVisiblePointTruthRevision:HK_BATTLE_VISIBLE_POINT_TRUTH_REV",
    "battle-target-safe-scroll-20260928-r1",
    "battle-full-fair-state-20260928-r1",
    "battle-egg-one-berry-buy-20260928-r1",
    "clan-crest-launcher-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

for forbidden in [
    "window.innerHeight*0.68",
    "cy>=top && cy<=Math.max(top+40,bottom)",
]:
    if forbidden in s:
        raise SystemExit("fixed viewport-band regression remains: "+forbidden)

p.write_text(s,encoding="utf-8")
print("BATTLE_VISIBLE_POINT_TRUTH_1_18_82=PASS")
