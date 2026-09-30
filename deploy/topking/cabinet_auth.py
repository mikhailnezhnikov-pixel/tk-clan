"""Targeted cabinet login diagnosis; never print credentials or user payloads."""
import ast
import argparse
import hashlib
import hmac
import json
import os
import re
import time
from pathlib import Path
import subprocess
import sqlite3
import urllib.error
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=('inspect', 'patch', 'test', 'verify'), default='inspect')
parser.add_argument('--source', default='/opt/hamsterking-license/server.py')
args = parser.parse_args()
source_path = Path(args.source)
source = source_path.read_text()
tree = ast.parse(source)
if args.mode == 'patch':
    old = 'audit("cabinet_login_failed", "telegram", ip, "invalid signature")'
    new = 'audit("cabinet_login_failed", "telegram", ip, "invalid or expired Telegram login")'
    assert source.count(old) == 1, 'Unexpected login audit anchor; refuse patch'
    source_path.write_text(source.replace(old, new))
    print('CABINET_AUTH_PATCH=PASS (audit detail only)')
    raise SystemExit(0)

def validator_tests(token='123456:test-token'):
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'verify_telegram_login')
    now = int(time.time())
    namespace = dict(TELEGRAM_BOT_TOKEN=token, TELEGRAM_ID_RE=re.compile(r'^[1-9][0-9]{4,19}$'),
                     re=re, hashlib=hashlib, hmac=hmac, utc_now=lambda: now)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source_path), 'exec'), namespace)
    verify = namespace['verify_telegram_login']
    def signed(**values):
        data = {'id': 9999999999999999999, 'auth_date': now, 'first_name': 'Тест 🐹', **values}
        # Explicit key sort, independently constructed according to Telegram Widget docs.
        check = '\n'.join(key + '=' + str(data[key]) for key in sorted(data))
        data['hash'] = hmac.new(hashlib.sha256(token.encode()).digest(), check.encode(), hashlib.sha256).hexdigest()
        return data
    valid = signed(last_name='Иванов', username='test_user', photo_url='https://example.org/photo?a=1&b=2')
    assert verify(valid)['id'] == '9999999999999999999'
    assert verify(dict(reversed(list(valid.items())))) is not None
    assert verify(signed()) is not None
    assert verify(signed(auth_date=now - 601)) is None
    assert verify(signed(auth_date=now + 61)) is None
    assert verify({**valid, 'first_name': 'Tampered'}) is None
    assert verify({**valid, 'hash': '0' * 64}) is None
    assert verify({**valid, 'hash': 'invalid'}) is None
    assert verify({**valid, 'auth_date': 'invalid'}) is None
    assert verify({**valid, 'id': 'invalid'}) is None
    assert verify({}) is None and verify(None) is None
    namespace['TELEGRAM_BOT_TOKEN'] = 'another-bot-token'
    assert verify(valid) is None
    print('TELEGRAM_WIDGET_REGRESSION=PASS (13 assertions)')
    return signed

if args.mode == 'test':
    validator_tests()
    raise SystemExit(0)

if args.mode == 'verify':
    pid = subprocess.check_output(['systemctl', 'show', 'hamsterking-license.service', '-p', 'MainPID', '--value'], text=True).strip()
    env = dict(item.split(b'=', 1) for item in Path(f'/proc/{pid}/environ').read_bytes().split(b'\0') if b'=' in item)
    token = env[b'HK_TELEGRAM_BOT_TOKEN'].decode().strip()
    signed = validator_tests(token)
    db_path = env.get(b'HK_LICENSE_DB', b'/var/lib/hamsterking-license/licenses.db').decode()
    def membership_snapshot():
        with sqlite3.connect('file:' + db_path + '?mode=ro', uri=True) as db:
            assert db.execute('SELECT 1 FROM clan_members WHERE telegram_id=?', ('9999999999999999999',)).fetchone() is None
            return db.execute('SELECT * FROM clan_members ORDER BY telegram_id').fetchall()
    before = membership_snapshot()
    base = 'https://hk-license.89.125.1.71.sslip.io/api/v1/cabinet'
    with urllib.request.urlopen(base + '/config', timeout=20) as response:
        config = json.load(response)
    assert config.get('enabled') and config.get('bot_username') == env[b'HK_TELEGRAM_BOT_USERNAME'].decode().lstrip('@')
    print('LIVE_CONFIG=PASS status=200')
    def probe(payload, expected_status, expected_error):
        request = urllib.request.Request(base + '/login', data=json.dumps({'telegram': payload}).encode(),
                    headers={'Origin': 'https://tk-clan.ru', 'Content-Type': 'application/json'})
        try:
            response = urllib.request.urlopen(request, timeout=20)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            result = json.load(response)
            assert response.code == expected_status and result.get('error') == expected_error, (response.code, result.get('error'))
        print('LIVE_LOGIN=PASS', expected_status, expected_error)
    # This is a synthetic signature test, never an impersonated allowed user.
    probe(signed(), 403, 'telegram_id_not_allowed')
    probe({**signed(), 'first_name': 'Tampered'}, 401, 'invalid_telegram_login')
    probe(signed(auth_date=int(time.time()) - 601), 401, 'invalid_telegram_login')
    assert membership_snapshot() == before, 'Membership changed during verification'
    print('ALLOWLIST_AND_ROLES_UNCHANGED=PASS')
    raise SystemExit(0)

for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in ('verify_telegram_login', 'audit', 'db_session', 'connect'):
        print(ast.get_source_segment(source, node))
pid = subprocess.check_output(['systemctl', 'show', 'hamsterking-license.service', '-p', 'MainPID', '--value'], text=True).strip()
env = dict(item.split(b'=', 1) for item in Path(f'/proc/{pid}/environ').read_bytes().split(b'\0') if b'=' in item)
token = env.get(b'HK_TELEGRAM_BOT_TOKEN', b'').decode().strip()
username = env.get(b'HK_TELEGRAM_BOT_USERNAME', b'').decode().strip().lstrip('@')
print('configured_bot_username', username)
try:
    with urllib.request.urlopen('https://api.telegram.org/bot' + token + '/getMe', timeout=15) as response:
        bot = json.load(response)
    actual = bot.get('result', {}).get('username', '')
    print('token_bot_username', actual)
    print('bot_identity_matches', actual.lower() == username.lower())
except Exception as exc:
    print('getMe_error', type(exc).__name__)
usage = os.statvfs('/var/lib/hamsterking-license')
print('disk_available_bytes', usage.f_bavail * usage.f_frsize)
db_path = env.get(b'HK_LICENSE_DB', b'/var/lib/hamsterking-license/licenses.db').decode()
print('service_uid', Path(f'/proc/{pid}/status').read_text().split('Uid:', 1)[1].splitlines()[0].strip())
for path in (Path(db_path).parent, Path(db_path)):
    stat = path.stat()
    print('database_permissions', str(path), stat.st_uid, stat.st_gid, oct(stat.st_mode & 0o777))
for suffix in ('', '-wal', '-shm'):
    path = Path(db_path + suffix)
    print('database_file', suffix or 'main', path.exists(), path.stat().st_size if path.exists() else 0)
for fd in Path(f'/proc/{pid}/fd').iterdir():
    try:
        target = os.readlink(fd)
        if db_path in target:
            print('database_open_fd', target)
    except OSError:
        pass
try:
    db = sqlite3.connect('file:' + db_path + '?mode=ro', uri=True, timeout=5)
    print('database_read', db.execute('SELECT count(*) FROM clan_members').fetchone()[0])
    print('database_journal', db.execute('PRAGMA journal_mode').fetchone()[0])
    db.close()
except sqlite3.Error as exc:
    print('database_read_error', str(exc))
logs = subprocess.check_output(['journalctl', '-u', 'hamsterking-license.service', '--since', '-15 min', '--no-pager', '-n', '150'], text=True)
for line in logs.splitlines():
    # Only standard exception classes; never dump request bodies or credentials.
    if 'sqlite3.' in line or 'NameError:' in line or 'TypeError:' in line or 'File "/opt/hamsterking-license/server.py"' in line:
        print('service_exception', line.split('python', 1)[-1][-250:])
