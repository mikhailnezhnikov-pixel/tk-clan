from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/HamsterKingMobile.user.js")
s=p.read_text(encoding="utf-8")

required=[
  "// @version      1.18.86",
  "battle-preview-resume-20260929-r1",
  "function autoMapBattlePreviewRoot()",
  "function autoMapResumeBattlePreview(",
  "battle-preview-start",
  "battle-preview-resumed",
  "сражение → запускаю",
  "document.elementFromPoint",
  "trader-gold-exact-purchase-modal-20260929-r1",
  "battle-intro-hard-gate-20260929-r1",
]
for marker in required:
    if marker not in s:
        raise SystemExit("battle preview resume contract broken: "+marker)

# The strict Gold Coins detector must verify that the matched modal is actually
# in front. Otherwise a stale merchant modal behind a Treasure Map preview can
# steal AutoMap ownership forever.
start=s.find("function traderForbiddenGoldModalRoot()")
end=s.find("function traderForbiddenGoldCloseButton",start)
block=s[start:end]
if "document.elementFromPoint" not in block:
    raise SystemExit("gold modal detector lacks foreground truth")
if "row.exactTitle && row.purchaseText" not in block:
    raise SystemExit("gold modal detector lost exact purchase-modal gate")

# An already-open Battle preview must be resumed before the intro hard gate and
# before generic route logic, so the 40-berry launch button cannot remain stuck.
start=s.find("async function runAutoMapTick(source='loop')")
end=s.find("function setAutoMapEnabled",start)
block=s[start:end]
preview=block.find("const openBattlePreview=autoMapBattlePreviewRoot();")
intro=block.find("const introHardGate=battleIntroModalRoot();")
if preview<0 or intro<0 or preview>intro:
    raise SystemExit("battle preview recovery does not outrank battle intro gate")

helper_start=s.find("async function autoMapResumeBattlePreview(")
helper_end=s.find("function autoMapTreasureKeyModalRoot()",helper_start)
helper=s[helper_start:helper_end]
for marker in [
  "autoMapModalPrimaryButton(root,null)",
  "dispatchAutoMapTap(action,'battle-preview-start')",
  "getSignature()",
  "runAutoMapTick('battle-preview-resumed')",
]:
    if marker not in helper:
        raise SystemExit("battle preview helper missing: "+marker)

for marker in [
  "battle-visible-point-truth-20260929-r1",
  "battle-full-fair-state-20260928-r1",
  "battle-egg-one-berry-buy-20260928-r1",
  "battle-strict-exit-gate-20260927-r1",
  "battle-reward-state-machine-20260928-r1",
  "trader-gold-stale-modal-reset-20260929-r1",
  "clan-crest-transparent-mask-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("preserved behavior missing: "+marker)

print("BATTLE_PREVIEW_RESUME_CONTRACT=PASS")
