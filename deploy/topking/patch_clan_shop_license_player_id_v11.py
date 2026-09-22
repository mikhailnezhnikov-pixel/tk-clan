from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text(encoding="utf-8")
MARKER="CLAN_SHOP_LICENSE_PLAYER_ID_V11"
if MARKER in s:
    print(MARKER+"_ALREADY_PRESENT")
    raise SystemExit(0)

if "CLAN_SHOP_PLAYER_ATTRIBUTION_V10" not in s:
    raise SystemExit("Clan Shop player attribution V10 missing")

# Add canonical license registry helper before linked identities helper.
anchor="def clan_shop_linked_identities() -> dict[str, dict]:\n"
helper='''def clan_shop_license_identities() -> dict[str, dict]:
    # CLAN_SHOP_LICENSE_PLAYER_ID_V11
    # Canonical identity: exact game player_id from the owner's license registry.
    # The owner's note is the display name for that ID.
    result={}
    with db_session() as db:
        rows=db.execute("""
            SELECT player_id,note,active
            FROM licenses
            WHERE player_id IS NOT NULL AND TRIM(player_id)<>''
        """).fetchall()
    for row in rows:
        player_id=str(row["player_id"] or "").strip()
        if not player_id:
            continue
        note=str(row["note"] or "").strip()
        result[player_id]={
            "player_id":player_id,
            "display_name":note,
            "note":note,
            "active":bool(row["active"]),
        }
    return result


'''
if anchor not in s:
    raise SystemExit("linked identity anchor missing")
s=s.replace(anchor,helper+anchor,1)

# Make license registry primary in participant list too.
old='''    linked_identities = clan_shop_linked_identities()
    result = []
'''
new='''    license_identities = clan_shop_license_identities()
    linked_identities = clan_shop_linked_identities()
    result = []
'''
if old not in s:
    raise SystemExit("participants identity map block missing")
s=s.replace(old,new,1)

old='''        linked = linked_identities.get(player_id) if player_id else None
        nickname = (str(linked.get("display_name") or "").strip() if linked else "") or snapshot_nickname
'''
new='''        licensed = license_identities.get(player_id) if player_id else None
        linked = linked_identities.get(player_id) if player_id else None
        nickname = (str(licensed.get("display_name") or "").strip() if licensed else "") \
            or (str(linked.get("display_name") or "").strip() if linked else "") \
            or snapshot_nickname
'''
if old not in s:
    raise SystemExit("participants nickname block missing")
s=s.replace(old,new,1)

old='''            "identity_source": "linked_player_id" if linked else "clan_snapshot",
'''
new='''            "identity_source": "license_player_id" if licensed and licensed.get("display_name") else (
                "linked_player_id" if linked and linked.get("display_name") else "clan_snapshot"
            ),
'''
if old in s:
    s=s.replace(old,new,1)

# V10 history payload: load direct ID registry and prefer it before linked member/snapshots.
old='''    linked_identities=clan_shop_linked_identities()

    latest_nickname_by_player_id={}
'''
new='''    license_identities=clan_shop_license_identities()
    linked_identities=clan_shop_linked_identities()

    latest_nickname_by_player_id={}
'''
if old not in s:
    raise SystemExit("V10 history identity prelude missing")
s=s.replace(old,new,1)

old='''        participant=by_player_id.get(pid)
        linked=linked_identities.get(pid)
        nickname=(
            str(linked.get("display_name") or "").strip() if linked else ""
        ) or (
            str(participant.get("nickname") or "").strip() if participant else ""
        ) or full_snapshot_nickname_by_player_id.get(pid,"") \
          or latest_nickname_by_player_id.get(pid,"") \
          or pid

        key=(week,"id:"+pid)
'''
new='''        participant=by_player_id.get(pid)
        licensed=license_identities.get(pid)
        linked=linked_identities.get(pid)
        nickname=(
            str(licensed.get("display_name") or "").strip() if licensed else ""
        ) or (
            str(linked.get("display_name") or "").strip() if linked else ""
        ) or (
            str(participant.get("nickname") or "").strip() if participant else ""
        ) or full_snapshot_nickname_by_player_id.get(pid,"") \
          or latest_nickname_by_player_id.get(pid,"") \
          or pid

        key=(week,"id:"+pid)
'''
if old not in s:
    raise SystemExit("V10 history nickname block missing")
s=s.replace(old,new,1)

old='''            "identity_source":"linked_player_id" if linked else (
                "clan_snapshot" if participant or pid in full_snapshot_nickname_by_player_id
                else ("skill_snapshot" if pid in latest_nickname_by_player_id else "player_id")
            ),
'''
new='''            "identity_source":"license_player_id" if licensed and licensed.get("display_name") else (
                "linked_player_id" if linked and linked.get("display_name") else (
                    "clan_snapshot" if participant or pid in full_snapshot_nickname_by_player_id
                    else ("skill_snapshot" if pid in latest_nickname_by_player_id else "player_id")
                )
            ),
'''
if old not in s:
    raise SystemExit("V10 history identity_source block missing")
s=s.replace(old,new,1)

path.write_text(s,encoding="utf-8")
print("CLAN_SHOP_LICENSE_PLAYER_ID_V11_PATCH_OK")
