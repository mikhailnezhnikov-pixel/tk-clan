from pathlib import Path

PATH=Path("/tmp/HamsterKingMobile.user.js")
s=PATH.read_text(encoding="utf-8")
MARKER="clan-snapshot-numeric-player-id-20260923-r1"

if MARKER in s:
    print("CLAN_SNAPSHOT_NUMERIC_PLAYER_ID_ALREADY_PRESENT")
    raise SystemExit(0)

for required in [
    "// @version      1.17.35",
    "const BUILD_VERSION = '1.17.35';",
    "const membersSource = Array.isArray(membersDocument?.clan_members)",
    "const memberId = clean(member.id ?? member.player_id ?? member.member_id ?? '');",
]:
    if required not in s:
        raise SystemExit("missing marker: "+required)

s=s.replace("// @version      1.17.35","// @version      1.17.36",1)
s=s.replace("const BUILD_VERSION = '1.17.35';","const BUILD_VERSION = '1.17.36';",1)

release="// @release-note После 429 автообновления модулей не повторяются до конца cooldown; Game API переходит на адаптивный медленный темп и не создаёт новый burst после восстановления."
s=s.replace(
    release,
    "// @release-note Clan Shop и статистика клана теперь сохраняют настоящий числовой player_id участника; внутренний opaque member.id больше не подменяет игровой ID.\n"+release,
    1
)

s=s.replace(
    "const memberId = clean(member.id ?? member.player_id ?? member.member_id ?? '');",
    "const memberId = clean(member.player_id ?? member.member_id ?? member.id ?? ''); // "+MARKER,
    1
)

for marker in [
    "// @version      1.17.36",
    "const BUILD_VERSION = '1.17.36';",
    MARKER,
    "const memberId = clean(member.player_id ?? member.member_id ?? member.id ?? '');"
]:
    if marker not in s:
        raise SystemExit("post-patch marker missing: "+marker)

PATH.write_text(s,encoding="utf-8")
print("CLAN_SNAPSHOT_NUMERIC_PLAYER_ID_R1=PASS")
