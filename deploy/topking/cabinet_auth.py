"""Targeted cabinet login diagnosis; never print credentials or user payloads."""
import ast
import json
import os
from pathlib import Path
import subprocess
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
logs = subprocess.check_output(['journalctl', '-u', 'hamsterking-license.service', '--since', '-15 min', '--no-pager', '-n', '150'], text=True)
for line in logs.splitlines():
    # Only standard exception classes; never dump request bodies or credentials.
    if 'sqlite3.' in line or 'NameError:' in line or 'TypeError:' in line:
        print('service_exception', line.split('python', 1)[-1][-250:])
