import ast
import os
from pathlib import Path
import subprocess
source = Path('/opt/hamsterking-license/server.py').read_text()
tree = ast.parse(source)
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        if node.name in ('cabinet_token', 'cabinet_member_from_token', 'verify_telegram_login', 'db_session', 'connect'):
            print(ast.get_source_segment(source, node))
        if isinstance(node, ast.ClassDef):
            for method in node.body:
                if isinstance(method, ast.FunctionDef) and method.name in ('do_GET','do_POST','do_OPTIONS','send_cabinet_json','cabinet_member'):
                    snippet = ast.get_source_segment(source, method)
                    print('HANDLER', node.name, method.name)
                    print(snippet if method.name not in ('do_GET','do_POST') else '\n'.join(snippet.splitlines()[:12]))
for line in source.splitlines():
    if line.startswith(('CABINET_SESSION_', 'CABINET_SECRET', 'TELEGRAM_ADMIN_CHAT_ID', 'TELEGRAM_BOT_USERNAME')):
        print(line)
pid = subprocess.check_output(['systemctl','show','hamsterking-license.service','-p','MainPID','--value'],text=True).strip()
env = dict(x.split(b'=',1) for x in Path('/proc/'+pid+'/environ').read_bytes().split(b'\0') if b'=' in x)
admin = env.get(b'HK_TELEGRAM_ADMIN_CHAT_ID',b'').decode().strip()
print('OWNER_ID_IS_PRIVATE_USER', admin.isdigit() and int(admin)>0)
print('SERVICE_ACTIVE', subprocess.call(['systemctl','is-active','--quiet','hamsterking-license.service'])==0)
print('DISK_AVAILABLE_BYTES',os.statvfs('/var/lib/hamsterking-license').f_bavail*os.statvfs('/var/lib/hamsterking-license').f_frsize)
