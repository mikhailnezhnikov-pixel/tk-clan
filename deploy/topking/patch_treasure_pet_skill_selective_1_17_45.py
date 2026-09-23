from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")
MARKER="treasure-guide-pet-skill-selective-20260923-r3"

if MARKER in s:
    print("TREASURE_PET_SKILL_SELECTIVE_ALREADY_PRESENT")
    raise SystemExit(0)

for required in [
    "// @version      1.17.44",
    "const BUILD_VERSION = '1.17.44';",
    "treasure-guide-selective-extract-20260923-r2",
    "function treasureGuideLooksRelevant(value)",
    "function treasureGuideSendSelective(path,body)"
]:
    if required not in s:
        raise SystemExit("missing marker: "+required)

s=s.replace("// @version      1.17.44","// @version      1.17.45",1)
s=s.replace("const BUILD_VERSION = '1.17.44';","const BUILD_VERSION = '1.17.45';",1)

needle="const HK_TREASURE_GUIDE_SELECTIVE_REV='treasure-guide-selective-extract-20260923-r2';"
s=s.replace(needle,needle+"\n  const HK_TREASURE_GUIDE_PET_SKILL_REV='"+MARKER+"';",1)

old_regex="return /treasure|treasurehunt|minigame|event_treasures|fair_treasures|pet_mission|golden_berry|карта.{0,16}сокровищ|сокровищ/i.test(String(value||''));"
new_regex="return /treasure|treasurehunt|minigame|event_treasures|fair_treasures|pet_mission|pet_skill|mf_pm_|golden_berry|карта.{0,16}сокровищ|сокровищ/i.test(String(value||''));"
if old_regex not in s:
    raise SystemExit("relevance regex missing")
s=s.replace(old_regex,new_regex,1)

old_paths="""    if(!['/quests','/shop/view','/client_config','/items','/events'].includes(path) &&
       !path.startsWith('/battlepass') &&
       !path.startsWith('/fair/'))return;"""
new_paths="""    if(!['/quests','/shop/view','/client_config','/items','/events'].includes(path) &&
       !path.startsWith('/battlepass') &&
       !path.startsWith('/fair/') &&
       !path.startsWith('/localization/'))return;"""
if old_paths not in s:
    raise SystemExit("selective path guard missing")
s=s.replace(old_paths,new_paths,1)

for marker in [
    "// @version      1.17.45",
    "const BUILD_VERSION = '1.17.45';",
    "treasure-guide-pet-skill-selective-20260923-r3",
    "pet_skill|mf_pm_",
    "!path.startsWith('/localization/')"
]:
    if marker not in s:
        raise SystemExit("post patch marker missing: "+marker)

PATH.write_text(s,encoding="utf-8")
print("TREASURE_PET_SKILL_SELECTIVE_1_17_45=PASS")
