from pathlib import Path
import base64, zlib, hashlib

path = Path("/tmp/HamsterKingMobile.user.js")
text = path.read_text(encoding="utf-8")

old_marker = "const HK_STAGE2J_BOSSES_REV = 'bosses-readonly-20260920-r1';"
new_marker = "const HK_STAGE2J_BOSSES_REV = 'bosses-canon-core-20260920-r1';"
if old_marker not in text:
    raise SystemExit("expected Bosses readonly marker not found")
text = text.replace(old_marker, new_marker, 1)

readonly_anchor = "    '/regional_boss/battle_state',"
if readonly_anchor not in text:
    list_anchor = "    '/clan/skill_lines/stats',\n"
    if list_anchor not in text:
        raise SystemExit("read-only POST whitelist anchor not found")
    text = text.replace(list_anchor, list_anchor + readonly_anchor + "\n", 1)

start_anchor = "  function bossStateRows(documentValue = bossSnapshot || hkStateStore.snapshot || playerDocument) {"
end_anchor = "      function renderWars() {"
start = text.find(start_anchor)
end = text.find(end_anchor, start)
if start < 0 or end < 0 or end <= start:
    raise SystemExit("Bosses readonly block anchors not found")

payload = Path("deploy/topking/boss_core_r1.zb64").read_text(encoding="utf-8").strip()
core_bytes = zlib.decompress(base64.b64decode(payload))
expected_core_sha = "c5805803e1c8b17c5b53cc873a8bdfd13ff05027c524b8d6b47a78eb6f012d19"
actual_core_sha = hashlib.sha256(core_bytes).hexdigest()
if actual_core_sha != expected_core_sha:
    raise SystemExit(f"Bosses core payload SHA mismatch: {actual_core_sha}")
replacement = core_bytes.decode("utf-8")
text = text[:start] + replacement + "\n      " + text[end:]

required = [
    "HK_BOSSES_CANON_REV='bosses-canon-core-20260920-r1'",
    "function bossCanonBuildPlans",
    "function bossCanonAskDecision",
    "async function bossCanonFinishAreaAttempt",
    "async function bossCanonFinishRegionalAttempt",
    "async function bossCanonRunArea",
    "async function bossCanonRunRegional",
    "async function runBossesCanonical",
    "'/bosses/battle'",
    "'/bosses/pass'",
    "'/bosses/respawn'",
    "'/regional_boss/battle_state'",
    "'/regional_boss/battle'",
    "'/player/regional_boss/pass'",
]
for needle in required:
    if needle not in text:
        raise SystemExit(f"missing invariant after patch: {needle}")

path.write_text(text, encoding="utf-8")
print("Bosses canonical core r1 patch applied")
