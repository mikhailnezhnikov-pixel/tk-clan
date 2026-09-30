"""Targeted cabinet login diagnosis; never print credentials or user payloads."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sqlite3
import urllib.request

source = Path('/opt/hamsterking-license/server.py').read_text()
tree = ast.parse(source)
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in ('verify_telegram_login', 'audit', 'db_session'):
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
