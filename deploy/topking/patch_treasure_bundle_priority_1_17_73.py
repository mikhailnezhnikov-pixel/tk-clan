from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")
MARKER="treasure-guide-priority-bundles-20260923-r1"

if MARKER in s:
    print("TREASURE_BUNDLE_PRIORITY_ALREADY_PRESENT")
    raise SystemExit(0)

for required in [
    "// @version      1.17.72",
    "const BUILD_VERSION = '1.17.72';",
    "treasure-guide-priority-lots-20260923-r1",
    "treasure-guide-priority-trader-lots-20260923-r1",
    "treasure-guide-priority-battlepass-lines-20260923-r1",
]:
    if required not in s:
        raise SystemExit("missing marker: "+required)

s=s.replace("// @version      1.17.72","// @version      1.17.73",1)
s=s.replace("const BUILD_VERSION = '1.17.72';","const BUILD_VERSION = '1.17.73';",1)

pos=s.find("// @release-note ")
if pos>=0:
    s=s[:pos]+"// @release-note Карта Сокровищ: четыре ограниченных набора магазина приоритетно сохраняются из уже загруженного /shop/view без дополнительных запросов к игре.\n"+s[pos:]

anchor="  const HK_TREASURE_GUIDE_PRIORITY_BATTLEPASS_REV='treasure-guide-priority-battlepass-lines-20260923-r1';\n"
insert=anchor+"  const HK_TREASURE_GUIDE_PRIORITY_BUNDLES_REV='treasure-guide-priority-bundles-20260923-r1';\n"
if anchor not in s:
    raise SystemExit("battlepass priority anchor missing")
s=s.replace(anchor,insert,1)

old="mf_treasurelot_trader_type_(?:01|02|03)_active_rep_5)$/;"
new="mf_treasurelot_trader_type_(?:01|02|03)_active_rep_5|mf_shoplot_treasure_offer_(?:pets_collection_10|energy_collection_10|keys_collection_10|maps_golden_berries_10))$/;"
if old not in s:
    raise SystemExit("wanted regex tail missing")
s=s.replace(old,new,1)

for marker in [
    "// @version      1.17.73",
    "const BUILD_VERSION = '1.17.73';",
    "HK_TREASURE_GUIDE_PRIORITY_BUNDLES_REV='treasure-guide-priority-bundles-20260923-r1'",
    "mf_shoplot_treasure_offer_(?:pets_collection_10|energy_collection_10|keys_collection_10|maps_golden_berries_10)"
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

PATH.write_text(s,encoding="utf-8")
print("TREASURE_BUNDLE_PRIORITY_1_17_73=PASS")
