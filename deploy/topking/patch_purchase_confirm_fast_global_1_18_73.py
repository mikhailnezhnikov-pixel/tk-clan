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
    "// @version      1.18.72",
    "// @version      1.18.73\n"
    "// @release-note Покупки в мини-играх: подтверждение любого покупаемого слота теперь отправляется через единый быстрый интервал 0,10–0,18 с после появления кнопки подтверждения. Это касается раскопок, сундуков, Тайного торговца, рыбалки и общих подтверждений Автокарты. Проверка результата, защита от двойного клика и cooldown после 409/429/5xx сохранены.",
    "version"
)
rep("const BUILD_VERSION = '1.18.72';","const BUILD_VERSION = '1.18.73';","build")

anchor="  const HK_TREASURE_DIG_FAST_REV='treasure-dig-fast-pacing-20260928-r1';"
rep(
    anchor,
    anchor+"\n  const HK_PURCHASE_CONFIRM_FAST_GLOBAL_REV='purchase-confirm-fast-global-20260928-r1';",
    "global purchase confirm revision"
)

# Global/AutoMap purchase-confirm pause.
rep("        confirm:[950,1650],","        confirm:[100,180],","generic confirm pacing")

# Fishing purchase-confirm pause.
rep("        confirm:[350,650],","        confirm:[100,180],","fishing confirm pacing")

# Trader purchase-confirm pause.
rep("        confirm:[300,520],","        confirm:[100,180],","trader confirm pacing")

# Chest purchase-confirm pause.
rep("        confirm:[650,1050],","        confirm:[100,180],","chest confirm pacing")

# Digging already had a dedicated fast path; make it exactly the same shared target.
rep("        confirm:[110,190],","        confirm:[100,180],","dig confirm pacing")

# Export revision for live diagnostics.
export_anchor="      treasureDigFastRevision:HK_TREASURE_DIG_FAST_REV,"
if s.count(export_anchor)!=1:
    raise SystemExit("dig export anchor missing")
s=s.replace(
    export_anchor,
    export_anchor+"\n      purchaseConfirmFastGlobalRevision:HK_PURCHASE_CONFIRM_FAST_GLOBAL_REV,",
    1
)

for marker in [
    "// @version      1.18.73",
    "const BUILD_VERSION = '1.18.73';",
    "purchase-confirm-fast-global-20260928-r1",
    "purchaseConfirmFastGlobalRevision:HK_PURCHASE_CONFIRM_FAST_GLOBAL_REV",
    "async function minigameHumanPause",
    "async function fishingHumanPause",
    "async function traderHumanPause",
    "async function chestHumanPause",
    "async function chestDigPause",
    "treasure-dig-fast-pacing-20260928-r1",
    "trader-receipt-ack-20260928-r1",
]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)

# Five purchase-confirm pacing helpers must now expose the same 100–180 ms interval.
if s.count("confirm:[100,180]") < 5:
    raise SystemExit(f"global confirm ranges missing: {s.count('confirm:[100,180]')}")

# Critical server/backoff and state-verification behavior must remain.
for marker in [
    "status===429",
    "minigameRandomMs(14000,19000)",
    "waitTreasureModal(target.cost,runId)",
    "waitTreasureActionButton(modal,target.cost,runId)",
    "CHEST_ACTION_TIMEOUT_MS",
    "waitDeviceNeutralCondition",
    "minigameRecentHttpError",
]:
    if marker not in s:
        raise SystemExit("safety marker missing: "+marker)

p.write_text(s,encoding="utf-8")
print("PURCHASE_CONFIRM_FAST_GLOBAL_1_18_73=PASS")
