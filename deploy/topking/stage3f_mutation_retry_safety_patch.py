from pathlib import Path

TARGET=Path('/tmp/HamsterKingMobile.user.js')
s=TARGET.read_text(encoding='utf-8')
REV='stage3f-mutation-retry-safety-20260920-r1'

def require(needle,message):
    if needle not in s:
        raise SystemExit(message)

if '// @version      1.16.13' not in s and '// @version      1.16.14' not in s:
    raise SystemExit('Stage 3F requires Stage 3E 1.16.13 or existing 1.16.14')
require("HK_STAGE3E_RESOURCES_REV = 'stage3e-resources-verify-20260920-r1'",'Stage 3E marker missing')
require('function hkIsMutationRequest(', 'mutation classifier missing')

if f"HK_STAGE3F_MUTATION_RETRY_REV = '{REV}'" not in s:
    s=s.replace('// @version      1.16.13','// @version      1.16.14',1)
    s=s.replace(": '1.16.13';",": '1.16.14';",1)
    marker="  const HK_STAGE3E_RESOURCES_REV = 'stage3e-resources-verify-20260920-r1';"
    require(marker,'Stage 3E marker anchor missing')
    s=s.replace(marker,marker+f"\n  const HK_STAGE3F_MUTATION_RETRY_REV = '{REV}';",1)
    runtime='  runtime.resourcesVerificationStage = HK_STAGE3E_RESOURCES_REV;'
    require(runtime,'Stage 3E runtime anchor missing')
    s=s.replace(runtime,runtime+"\n  runtime.mutationRetrySafetyStage = HK_STAGE3F_MUTATION_RETRY_REV;",1)

# A lost response to an irreversible mutation is ambiguous: the server may
# already have applied it. Never repeat such a request automatically.
old="""    return hkMutationGate.run(
      path,
      () => apiJsonCore(path, method, body, retryAuthorization, retryNetwork)
    );"""
new="""    return hkMutationGate.run(
      path,
      () => apiJsonCore(path, method, body, retryAuthorization, 0)
    );"""
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('mutation retry routing anchor missing')

checks=[
    ('// @version      1.16.14','version missing'),
    (f"HK_STAGE3F_MUTATION_RETRY_REV = '{REV}'",'marker missing'),
    ('() => apiJsonCore(path, method, body, retryAuthorization, 0)','mutations can still network-retry'),
    ("'/player/me'",'read-only player state path lost'),
    ("'/player/building'",'read-only building path lost'),
    ("GROWTH_HAMSTER_BUDGET_ID = 'cur_cap'",'Hamster Caps invariant lost'),
    ("GROWTH_GENERAL_BUDGET_ID = 'item_pit_token'",'General Pit Token invariant lost'),
]
for needle,message in checks:
    require(needle,message)
if "    '/player/event'" in s:
    raise SystemExit('/player/event must not be read-only')

TARGET.write_text(s,encoding='utf-8')
