from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text()
MARKER = "CLAN_SHOP_TEST_HISTORY_RESET_V1"
if MARKER in s:
    print("CLAN_SHOP_TEST_HISTORY_RESET_ALREADY_PRESENT")
    raise SystemExit(0)

anchor = '\ndef clan_shop_history_payload() -> dict:\n'
helper = r'''
# CLAN_SHOP_TEST_HISTORY_RESET_V1
def reset_clan_shop_test_history(member: dict) -> dict:
    if not clan_shop_can_manage(member):
        raise PermissionError("clan shop manage denied")
    ensure_clan_shop_schema()
    with db_session() as db:
        history_count = db.execute(
            "SELECT COUNT(*) AS c FROM clan_shop_publication_items"
        ).fetchone()["c"]
        publication_count = db.execute(
            "SELECT COUNT(*) AS c FROM clan_shop_publications"
        ).fetchone()["c"]
        db.execute("DELETE FROM clan_shop_publication_items")
        db.execute("DELETE FROM clan_shop_publications")
    return {
        "ok": True,
        "history_deleted": int(history_count or 0),
        "publication_weeks_deleted": int(publication_count or 0),
    }


'''
if anchor not in s:
    raise SystemExit("history payload anchor missing")
s=s.replace(anchor,'\n'+helper+'def clan_shop_history_payload() -> dict:\n',1)

post_anchor='''            elif path in ("/api/v1/cabinet/clan-shop/set",
                             "/api/v1/cabinet/clan-shop/request",
                             "/api/v1/cabinet/clan-shop/accept-request",
                             "/api/v1/cabinet/clan-shop/publish"):
'''
post_new='''            elif path == "/api/v1/cabinet/clan-shop/reset-test-history":
                origin = self.headers.get("Origin", "")
                if origin not in CABINET_ORIGINS:
                    self.send_cabinet_json(HTTPStatus.FORBIDDEN, {"error": "origin_not_allowed"}); return
                member = self.cabinet_member()
                if not member:
                    self.send_cabinet_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"}); return
                try:
                    result = reset_clan_shop_test_history(member)
                    audit("cabinet_clan_shop_test_history_reset", "all",
                          self.client_ip(),
                          f"history={result['history_deleted']} publications={result['publication_weeks_deleted']}")
                    self.send_cabinet_json(HTTPStatus.OK, result)
                except PermissionError:
                    self.send_cabinet_json(HTTPStatus.FORBIDDEN, {"error": "clan_shop_manage_denied"})
            elif path in ("/api/v1/cabinet/clan-shop/set",
                             "/api/v1/cabinet/clan-shop/request",
                             "/api/v1/cabinet/clan-shop/accept-request",
                             "/api/v1/cabinet/clan-shop/publish"):
'''
if post_anchor not in s:
    raise SystemExit("clan shop post anchor missing")
s=s.replace(post_anchor,post_new,1)

path.write_text(s)
print("CLAN_SHOP_TEST_HISTORY_RESET_PATCH_OK")
