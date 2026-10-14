"""Safely integrate the separate birthday module into the existing live server.py."""
from pathlib import Path
import sys

MARKER = "TOPKING_BIRTHDAYS_V1"
path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")

if MARKER in source:
    assert source.count(MARKER) == 2, "unexpected partial birthday integration"
    print("TOPKING_BIRTHDAY_PATCH=ALREADY_PRESENT")
    raise SystemExit(0)

anchor = '    command = command.split("@", 1)[0]\n'
if source.count(anchor) != 1:
    raise SystemExit("Birthday command hook anchor changed; refusing patch")
hook = '''    command = command.split("@", 1)[0]

    # TOPKING_BIRTHDAYS_V1: birthday commands precede the group-silence guard.
    if command in ("/birthday", "/mybirthday", "/birthdays",
                   "/deletebirthday", "/birthdayhelp"):
        from topking_birthdays import handle_command as birthday_handle_command
        if birthday_handle_command(command, text, chat, user, telegram_send,
                                   message_thread_id=message.get("message_thread_id")):
            return
'''
source = source.replace(anchor, hook, 1)

anchor = '        ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()\n'
if source.count(anchor) != 1:
    raise SystemExit("Birthday startup hook anchor changed; refusing patch")
replacement = '''        # TOPKING_BIRTHDAYS_V1: catch up after restart; one daemon per process.
        from topking_birthdays import start_birthday_scheduler
        start_birthday_scheduler(telegram_send)
        ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
'''
source = source.replace(anchor, replacement, 1)
compile(source, str(path), "exec")
path.write_text(source, encoding="utf-8")
print("TOPKING_BIRTHDAY_PATCH=PASS")
