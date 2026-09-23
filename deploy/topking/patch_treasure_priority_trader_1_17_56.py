from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")
MARKER="treasure-guide-priority-trader-lots-20260923-r1"

if MARKER in s:
    print("TREASURE_TRADER_PRIORITY_ALREADY_PRESENT")
    raise SystemExit(0)

for required in [
    "// @version      1.17.55",
    "const BUILD_VERSION = '1.17.55';",
    "treasure-guide-priority-lots-20260923-r1",
    "режим 3/6/9 теперь ждёт полную выбранную комбинацию",
]:
    if required not in s:
        raise SystemExit("missing marker: "+required)

s=s.replace("// @version      1.17.55","// @version      1.17.56",1)
s=s.replace("const BUILD_VERSION = '1.17.55';","const BUILD_VERSION = '1.17.56';",1)

release="// @release-note Карта Сокровищ: полные лоты Тайного торговца приоритетно сохраняются из уже загруженного /shop/view без дополнительных запросов к игре.\n"
pos=s.find("// @release-note ")
if pos>=0:
    s=s[:pos]+release+s[pos:]

old="  const HK_TREASURE_GUIDE_PRIORITY_LOTS_REV='treasure-guide-priority-lots-20260923-r1';\n"
new=old+"  const HK_TREASURE_GUIDE_PRIORITY_TRADER_REV='treasure-guide-priority-trader-lots-20260923-r1';\n"
if old not in s:
    raise SystemExit("priority marker anchor missing")
s=s.replace(old,new,1)

old_regex="    const wanted=/^(?:mf_fair_treasury_room_choose_way_[123]|mf_treasurelot_chest_type_(?:01|015|02|03)|mf_treasurelot_chest_digging_spot_sl[4-9])$/;\n"
new_regex="    const wanted=/^(?:mf_fair_treasury_room_choose_way_[123]|mf_treasurelot_chest_type_(?:01|015|02|03)|mf_treasurelot_chest_digging_spot_sl[4-9]|mf_fairlot_minigame_trader_(?:01|02|03)_.+|mf_treasurelot_trader_type_(?:01|02|03)_active_rep_5)$/;\n"
if old_regex not in s:
    raise SystemExit("priority regex anchor missing")
s=s.replace(old_regex,new_regex,1)

for marker in [
    "// @version      1.17.56",
    "const BUILD_VERSION = '1.17.56';",
    "HK_TREASURE_GUIDE_PRIORITY_TRADER_REV='treasure-guide-priority-trader-lots-20260923-r1'",
    "mf_fairlot_minigame_trader_(?:01|02|03)_.+",
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

PATH.write_text(s,encoding="utf-8")
print("TREASURE_TRADER_PRIORITY_1_17_56=PASS")
