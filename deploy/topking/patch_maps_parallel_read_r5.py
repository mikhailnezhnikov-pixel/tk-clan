from pathlib import Path

TARGET=Path('/tmp/HamsterKingMobile.user.js')
s=TARGET.read_text(encoding='utf-8')

def require(needle,message):
    if needle not in s:
        raise SystemExit(message)

require("HK_MAP_SCANNER_REV = 'maps-parallel-read-20260920-r4'","scanner r4 missing")
require("const HK_MAP_READ_CONCURRENCY = 6;","r4 concurrency missing")
require("const HK_MAP_SUBMIT_BATCH = 100;","r4 batch missing")
require("HK_MAP_COORDS_REV = 'maps-coordinates-column-row-20260920-r1'","coords r1 missing")

s=s.replace("HK_MAP_SCANNER_REV = 'maps-parallel-read-20260920-r4'",
            "HK_MAP_SCANNER_REV = 'maps-parallel-read-20260920-r5'",1)
s=s.replace("const HK_MAP_READ_CONCURRENCY = 6;",
            "const HK_MAP_READ_CONCURRENCY = 10;",1)
s=s.replace("const HK_MAP_SUBMIT_BATCH = 100;",
            "const HK_MAP_SUBMIT_BATCH = 200;",1)

require("HK_MAP_SCANNER_REV = 'maps-parallel-read-20260920-r5'","scanner r5 marker missing")
require("const HK_MAP_READ_CONCURRENCY = 10;","r5 concurrency missing")
require("const HK_MAP_SUBMIT_BATCH = 200;","r5 batch missing")
require("activePlayerBuildingIds(state)","safe active intersection lost")
require("ensureCrystalEventCatalog()","event catalog guard lost")
require("Promise.all(Array.from({length:workers},()=>worker()))","parallel workers lost")
require("hkMutationGate.run('/player/building'","explicit opening gate lost")
require("HK_MAP_COORDS_REV = 'maps-coordinates-column-row-20260920-r1'","coords invariant lost")
require("HK_BUILDINGS_CANON_REV = 'buildings-canon-core-20260920-r1'","buildings invariant lost")
require("HK_STAGE2J_BOSSES_REV = 'bosses-area-target-20260920-r2'","bosses invariant lost")
require("HK_PITS_REWARD_PICKER_REV = 'pits-reward-picker-20260920-r20'","pits invariant lost")

TARGET.write_text(s,encoding='utf-8')
