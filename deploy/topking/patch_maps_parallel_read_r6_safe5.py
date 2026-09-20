from pathlib import Path

p=Path("/tmp/HamsterKingMobile.user.js")
s=p.read_text()

old_rev="const HK_MAP_SCANNER_REV = 'maps-parallel-read-20260920-r5';"
new_rev="const HK_MAP_SCANNER_REV = 'maps-parallel-read-20260920-r6-safe5';"
old_conc="const HK_MAP_READ_CONCURRENCY = 10;"
new_conc="const HK_MAP_READ_CONCURRENCY = 5;"

assert s.count(old_rev)==1, s.count(old_rev)
assert s.count(old_conc)==1, s.count(old_conc)

s=s.replace(old_rev,new_rev,1).replace(old_conc,new_conc,1)

assert "const HK_MAP_SUBMIT_BATCH = 200;" in s
assert "explore-readonly-plan-20260920-r4-ui" in s
p.write_text(s)
