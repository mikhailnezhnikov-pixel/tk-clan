from pathlib import Path
import re, sys

path = Path(sys.argv[1])
s = path.read_text()
MARKER = 'SCOPED_HK_MAP_ACCESS_V1'
if MARKER in s:
    print('scoped access patch already present')
    raise SystemExit(0)

helpers = r'''
# SCOPED_HK_MAP_ACCESS_V1

def ensure_scoped_hk_map_access_schema() -> None:
    now = utc_now()
    with db_session() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS hk_map_access_rules (
                telegram_id TEXT NOT NULL,
                scope_type TEXT NOT NULL CHECK(scope_type IN ('city','map')),
                scope_value TEXT NOT NULL,
                allowed INTEGER NOT NULL DEFAULT 1,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                PRIMARY KEY (telegram_id, scope_type, scope_value),
                FOREIGN KEY (telegram_id) REFERENCES clan_members(telegram_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_hk_map_access_rules_member
                ON hk_map_access_rules(telegram_id, scope_type, allowed);
            CREATE TABLE IF NOT EXISTS hk_map_access_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at INTEGER NOT NULL
            );
        """)
        migrated = db.execute("SELECT 1 FROM hk_map_access_meta WHERE key='legacy_full_access_v1'").fetchone()
        if not migrated:
            cities = [row[0] for row in db.execute("SELECT DISTINCT city FROM hk_maps_catalog ORDER BY city").fetchall()]
            legacy = [row[0] for row in db.execute(
                "SELECT telegram_id FROM clan_members WHERE active=1 AND maps_access=1 AND maps_manage=0"
            ).fetchall()]
            for telegram_id in legacy:
                for city in cities:
                    db.execute("""INSERT OR IGNORE INTO hk_map_access_rules
                                  (telegram_id,scope_type,scope_value,allowed,created_at,updated_at)
                                  VALUES(?,?,?,?,?,?)""",
                               (telegram_id, 'city', city, 1, now, now))
            db.execute("INSERT INTO hk_map_access_meta(key,value,updated_at) VALUES('legacy_full_access_v1','1',?)", (now,))
        db.execute("""UPDATE clan_members
                      SET maps_access=CASE
                          WHEN maps_manage=1 THEN 1
                          WHEN EXISTS(SELECT 1 FROM hk_map_access_rules r
                                      WHERE r.telegram_id=clan_members.telegram_id AND r.allowed=1) THEN 1
                          ELSE 0 END""")


def _hk_member_rules(db: sqlite3.Connection, telegram_id: str) -> tuple[set[str], dict[str, bool]]:
    rows = db.execute("""SELECT scope_type,scope_value,allowed FROM hk_map_access_rules
                         WHERE telegram_id=?""", (telegram_id,)).fetchall()
    cities: set[str] = set()
    maps: dict[str, bool] = {}
    for row in rows:
        if row['scope_type'] == 'city' and row['allowed']:
            cities.add(row['scope_value'])
        elif row['scope_type'] == 'map':
            maps[row['scope_value']] = bool(row['allowed'])
    return cities, maps


def member_can_access_hk_map(member: dict | None, map_key: str, city: str | None = None) -> bool:
    if not member:
        return False
    if member.get('maps_manage'):
        return True
    telegram_id = str(member.get('telegram_id') or '')
    if not TELEGRAM_ID_RE.fullmatch(telegram_id):
        return False
    ensure_scoped_hk_map_access_schema()
    with db_session() as db:
        if city is None:
            row = db.execute("SELECT city FROM hk_maps_catalog WHERE map_key=?", (map_key,)).fetchone()
            if not row:
                return False
            city = row['city']
        cities, maps = _hk_member_rules(db, telegram_id)
    if map_key in maps:
        return maps[map_key]
    return city in cities


def set_member_map_scope(member: dict, telegram_id: str, scope_type: str, scope_value: str, allowed: bool) -> dict:
    if not member.get('maps_manage'):
        raise PermissionError('maps manage denied')
    if not TELEGRAM_ID_RE.fullmatch(telegram_id):
        raise ValueError('invalid telegram id')
    scope_type = str(scope_type or '').strip().lower()
    scope_value = str(scope_value or '').strip()
    if scope_type not in ('city','map') or not scope_value:
        raise ValueError('invalid map scope')
    ensure_scoped_hk_map_access_schema()
    now = utc_now()
    with db_session() as db:
        target = db.execute("SELECT maps_manage FROM clan_members WHERE telegram_id=? AND active=1", (telegram_id,)).fetchone()
        if not target:
            raise LookupError('member not found')
        if target['maps_manage']:
            raise PermissionError('manager access is implicit')
        if scope_type == 'city':
            exists = db.execute("SELECT 1 FROM hk_maps_catalog WHERE city=? LIMIT 1", (scope_value,)).fetchone()
            if not exists:
                raise LookupError('city not found')
            city_maps = [row[0] for row in db.execute("SELECT map_key FROM hk_maps_catalog WHERE city=?", (scope_value,)).fetchall()]
            if city_maps:
                placeholders = ','.join('?' for _ in city_maps)
                db.execute(f"DELETE FROM hk_map_access_rules WHERE telegram_id=? AND scope_type='map' AND scope_value IN ({placeholders})",
                           (telegram_id, *city_maps))
            if allowed:
                db.execute("""INSERT INTO hk_map_access_rules(telegram_id,scope_type,scope_value,allowed,created_at,updated_at)
                              VALUES(?,?,?,?,?,?)
                              ON CONFLICT(telegram_id,scope_type,scope_value)
                              DO UPDATE SET allowed=excluded.allowed,updated_at=excluded.updated_at""",
                           (telegram_id,'city',scope_value,1,now,now))
            else:
                db.execute("DELETE FROM hk_map_access_rules WHERE telegram_id=? AND scope_type='city' AND scope_value=?",
                           (telegram_id,scope_value))
        else:
            map_row = db.execute("SELECT city FROM hk_maps_catalog WHERE map_key=?", (scope_value,)).fetchone()
            if not map_row:
                raise LookupError('map not found')
            city_rule = db.execute("""SELECT allowed FROM hk_map_access_rules
                                      WHERE telegram_id=? AND scope_type='city' AND scope_value=?""",
                                   (telegram_id,map_row['city'])).fetchone()
            city_allowed = bool(city_rule and city_rule['allowed'])
            if allowed and city_allowed:
                db.execute("DELETE FROM hk_map_access_rules WHERE telegram_id=? AND scope_type='map' AND scope_value=?",
                           (telegram_id,scope_value))
            elif allowed:
                db.execute("""INSERT INTO hk_map_access_rules(telegram_id,scope_type,scope_value,allowed,created_at,updated_at)
                              VALUES(?,?,?,?,?,?)
                              ON CONFLICT(telegram_id,scope_type,scope_value)
                              DO UPDATE SET allowed=excluded.allowed,updated_at=excluded.updated_at""",
                           (telegram_id,'map',scope_value,1,now,now))
            elif city_allowed:
                db.execute("""INSERT INTO hk_map_access_rules(telegram_id,scope_type,scope_value,allowed,created_at,updated_at)
                              VALUES(?,?,?,?,?,?)
                              ON CONFLICT(telegram_id,scope_type,scope_value)
                              DO UPDATE SET allowed=excluded.allowed,updated_at=excluded.updated_at""",
                           (telegram_id,'map',scope_value,0,now,now))
            else:
                db.execute("DELETE FROM hk_map_access_rules WHERE telegram_id=? AND scope_type='map' AND scope_value=?",
                           (telegram_id,scope_value))
        has_allow = db.execute("SELECT 1 FROM hk_map_access_rules WHERE telegram_id=? AND allowed=1 LIMIT 1", (telegram_id,)).fetchone()
        db.execute("UPDATE clan_members SET maps_access=?,updated_at=? WHERE telegram_id=?",
                   (1 if has_allow else 0, now, telegram_id))
    return {'ok': True, 'telegram_id': telegram_id, 'scope_type': scope_type,
            'scope_value': scope_value, 'allowed': bool(allowed)}

'''

needle = '\ndef cabinet_maps(member: dict) -> dict:\n'
if needle not in s:
    raise SystemExit('cabinet_maps anchor missing')
s = s.replace(needle, '\n' + helpers + 'def cabinet_maps(member: dict) -> dict:\n', 1)

new_cabinet = r'''def cabinet_maps(member: dict) -> dict:
    ensure_scoped_hk_map_access_schema()
    with db_session() as db:
        rows = db.execute("SELECT * FROM hk_maps_catalog ORDER BY score DESC,city,grid").fetchall()
        if not member.get('maps_manage'):
            telegram_id = str(member.get('telegram_id') or '')
            cities, map_rules = _hk_member_rules(db, telegram_id)
            rows = [row for row in rows if map_rules.get(row['map_key'], row['city'] in cities)]
            if not rows:
                raise PermissionError('maps access denied')
        members = []
        if member.get('maps_manage'):
            raw_members = [dict(row) for row in db.execute(
                """SELECT telegram_id,note,first_name,username,linked_player_id,active,maps_access,maps_manage
                   FROM clan_members WHERE active=1 ORDER BY first_name,username,note,telegram_id""").fetchall()]
            rule_rows = db.execute("SELECT telegram_id,scope_type,scope_value,allowed FROM hk_map_access_rules").fetchall()
            by_member: dict[str, dict] = {}
            for rule in rule_rows:
                bucket = by_member.setdefault(rule['telegram_id'], {'cities': [], 'maps': {}})
                if rule['scope_type'] == 'city' and rule['allowed']:
                    bucket['cities'].append(rule['scope_value'])
                elif rule['scope_type'] == 'map':
                    bucket['maps'][rule['scope_value']] = bool(rule['allowed'])
            for item in raw_members:
                rules = by_member.get(item['telegram_id'], {'cities': [], 'maps': {}})
                rules['cities'] = sorted(set(rules['cities']))
                item['map_rules'] = rules
                members.append(item)
    return {'ok': True, 'can_manage': bool(member.get('maps_manage')),
            'maps': [hk_map_row(row) for row in rows], 'members': members}
'''
s, n = re.subn(r'def cabinet_maps\(member: dict\) -> dict:\n.*?(?=\ndef public_maps\()', new_cabinet + '\n', s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('cabinet_maps replacement failed')

s = s.replace(
    '    if not public and (not member or not (member.get("maps_access") or member.get("maps_manage"))):\n        raise PermissionError("maps access denied")\n',
    '    if not public and not member:\n        raise PermissionError("maps access denied")\n',
    1
)
anchor = '    if not row:\n        raise LookupError("map not found")\n    full = load_full_hk_map(map_key)\n'
if anchor not in s:
    raise SystemExit('hk_map_data row anchor missing')
s = s.replace(anchor,
    '    if not row:\n        raise LookupError("map not found")\n'
    '    if not public and not member_can_access_hk_map(member, map_key, row["city"]):\n'
    '        raise PermissionError("maps access denied")\n'
    '    full = load_full_hk_map(map_key)\n', 1)

s = s.replace(
    '            if not (member.get("maps_access") or member.get("maps_manage")):\n                self.send_cabinet_json(HTTPStatus.FORBIDDEN, {"error": "maps_access_denied"}); return\n            key = parse_qs(parsed.query).get("key", [""])[0].strip()\n',
    '            key = parse_qs(parsed.query).get("key", [""])[0].strip()\n',
    1
)
route_anchor = '''            try:
                self.send_cabinet_json(HTTPStatus.OK, hk_map_data(key, member=member))
            except ValueError:
                self.send_cabinet_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_map_key"})
'''
if route_anchor not in s:
    raise SystemExit('private map data route anchor missing')
s = s.replace(route_anchor,
'''            try:
                self.send_cabinet_json(HTTPStatus.OK, hk_map_data(key, member=member))
            except PermissionError:
                self.send_cabinet_json(HTTPStatus.FORBIDDEN, {"error": "maps_access_denied"})
            except ValueError:
                self.send_cabinet_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_map_key"})
''', 1)

old_tuple = '("/api/v1/cabinet/maps/publish", "/api/v1/cabinet/maps/member-access", "/api/v1/cabinet/maps/open-url")'
new_tuple = '("/api/v1/cabinet/maps/publish", "/api/v1/cabinet/maps/member-access", "/api/v1/cabinet/maps/access-scope", "/api/v1/cabinet/maps/open-url")'
if old_tuple not in s:
    raise SystemExit('map POST route tuple missing')
s = s.replace(old_tuple, new_tuple, 1)
old_branch = '''                    elif path.endswith("/member-access"):
                        result = set_member_maps_access(member, str(body.get("telegram_id", "")).strip(), bool(body.get("allowed")))
                        audit("cabinet_maps_access", str(body.get("telegram_id", "")), self.client_ip(), f"allowed={int(bool(body.get('allowed')))}")
                    else:
'''
if old_branch not in s:
    raise SystemExit('member-access branch missing')
new_branch = '''                    elif path.endswith("/member-access"):
                        result = set_member_maps_access(member, str(body.get("telegram_id", "")).strip(), bool(body.get("allowed")))
                        audit("cabinet_maps_access", str(body.get("telegram_id", "")), self.client_ip(), f"allowed={int(bool(body.get('allowed')))}")
                    elif path.endswith("/access-scope"):
                        result = set_member_map_scope(
                            member, str(body.get("telegram_id", "")).strip(),
                            str(body.get("scope_type", "")).strip(), str(body.get("scope_value", "")).strip(),
                            bool(body.get("allowed"))
                        )
                        audit("cabinet_map_scope_access", str(body.get("telegram_id", "")), self.client_ip(),
                              f"{body.get('scope_type','')}={body.get('scope_value','')} allowed={int(bool(body.get('allowed')))}")
                    else:
'''
s = s.replace(old_branch, new_branch, 1)

path.write_text(s)
print('SCOPED_MAP_ACCESS_PATCH_OK')
