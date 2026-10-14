"""Offline regression suite: no Telegram requests, no production DB."""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULE = ROOT / "topking_birthdays.py"
PATCH = ROOT / "patch_topking_birthdays.py"

spec = importlib.util.spec_from_file_location("topking_birthdays", MODULE)
birth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(birth)


class Birthdays(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        birth.DB_FILE = Path(self.temp.name) / "birthdays.sqlite3"
        self.messages = []
        self.chat = {"id": -100987654321, "type": "supergroup"}
        self.user = {"id": 12345, "first_name": "Миша", "last_name": "<King>"}

    def send(self, chat_id, text, message_thread_id=None):
        self.messages.append((str(chat_id), text, message_thread_id))
        return True

    def command(self, cmd, text=None, user=None, chat=None):
        return birth.handle_command(cmd, text or cmd, chat or self.chat,
                                    user or self.user, self.send, 17)

    def test_create_update_delete_own_date(self):
        self.assertTrue(self.command("/birthday", "/birthday 02.10"))
        self.assertIn("02.10", self.messages[-1][1])
        self.assertIn("&lt;King&gt;", self.messages[-1][1])
        self.command("/mybirthday")
        self.assertIn("02.10", self.messages[-1][1])
        self.command("/birthday", "/birthday 29.02")
        self.command("/mybirthday")
        self.assertIn("29.02", self.messages[-1][1])
        self.command("/deletebirthday")
        self.command("/mybirthday")
        self.assertIn("ещё не сохранена", self.messages[-1][1])
        self.assertFalse(self.command("/start"))

    def test_invalid_dates_and_private_chat(self):
        for bad in ("31.02", "31.11", "00.10", "30.13", "29/02", "12.12.2020"):
            self.command("/birthday", "/birthday " + bad)
            self.assertIn("Неверная", self.messages[-1][1])
        self.command("/birthday", "/birthday 01.01",
                     chat={"id": 12345, "type": "private"})
        self.assertIn("в группе", self.messages[-1][1])
        with birth._connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM topking_birthdays").fetchone()[0], 0)

    def test_group_and_user_isolation(self):
        self.command("/birthday", "/birthday 14.10")
        other = {"id": 222, "first_name": "Друг"}
        self.command("/mybirthday", user=other)
        self.assertIn("ещё не сохранена", self.messages[-1][1])
        self.command("/deletebirthday", user=other)
        self.command("/mybirthday")
        self.assertIn("14.10", self.messages[-1][1])
        self.command("/mybirthday", chat={"id": -10012, "type": "group"})
        self.assertIn("ещё не сохранена", self.messages[-1][1])

    def test_full_list_not_15_and_telegram_chunks(self):
        for i in range(52):
            user = {"id": 1000+i, "first_name": "Игрок" + str(i)}
            self.command("/birthday", "/birthday 15.10", user=user)
        self.messages.clear()
        self.command("/birthdays")
        all_text = "\n".join(row[1] for row in self.messages)
        self.assertEqual(all_text.count("• Игрок"), 52)
        self.assertGreater(len(self.messages), 1)
        self.assertTrue(all(len(row[1]) < 3500 for row in self.messages))
        self.assertTrue(all(row[2] == 17 for row in self.messages))

    def test_0900_yakutsk_restart_catchup_and_no_duplicates(self):
        self.command("/birthday", "/birthday 14.10")
        self.messages.clear()
        early = datetime(2026, 10, 14, 8, 59, tzinfo=birth.YAKUTSK)
        now = datetime(2026, 10, 14, 11, 45, tzinfo=birth.YAKUTSK)
        self.assertEqual(birth.send_due_greetings(self.send, early), 0)
        self.assertEqual(birth.send_due_greetings(self.send, now), 1)
        self.assertIn('tg://user?id=12345', self.messages[-1][1])
        self.assertIn("&lt;King&gt;", self.messages[-1][1])
        self.assertEqual(birth.send_due_greetings(self.send, now), 0)
        self.command("/deletebirthday")
        self.command("/birthday", "/birthday 14.10")
        self.assertEqual(birth.send_due_greetings(self.send, now), 0)

    def test_failed_delivery_retries_and_uncertain_claim_never_duplicates(self):
        self.command("/birthday", "/birthday 14.10")
        now = datetime(2026, 10, 14, 9, 0, tzinfo=birth.YAKUTSK)
        self.assertEqual(birth.send_due_greetings(lambda *_: False, now), 0)
        self.assertEqual(birth.send_due_greetings(self.send, now), 1)
        self.assertEqual(birth.send_due_greetings(self.send, now), 0)
        other = {"id": 555, "first_name": "Crash"}
        self.command("/birthday", "/birthday 14.10", user=other)
        self.assertTrue(birth._claim(self.chat["id"], 555, 2026, int(now.timestamp())))
        self.assertEqual(birth.send_due_greetings(self.send, now), 0)

    def test_leap_day_only_on_leap_year(self):
        self.command("/birthday", "/birthday 29.02")
        leap = datetime(2028, 2, 29, 10, 0, tzinfo=birth.YAKUTSK)
        self.assertEqual(birth.send_due_greetings(self.send, leap), 1)
        self.assertEqual(birth.send_due_greetings(self.send, leap), 0)
        self.assertEqual(birth._next_occurrence(29, 2, leap.date()).year, 2028)

    def test_patch_preserves_other_handlers_and_is_idempotent(self):
        fixture = '''def handle_telegram_update(update):
    command = command.split("@", 1)[0]
    if command == "/setapplications":
        pass
    # TELEGRAM_GROUP_SILENCE_V2
    if chat.get("type") in ("group", "supergroup", "channel"):
        return

if __name__ == "__main__":
    if "--self-test" in os.sys.argv:
        pass
    else:
        ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
'''
        target = Path(self.temp.name) / "server.py"
        target.write_text(fixture)
        subprocess.run([sys.executable, str(PATCH), str(target)], check=True,
                       capture_output=True, text=True)
        patched = target.read_text()
        self.assertIn("TOPKING_BIRTHDAYS_V1", patched)
        self.assertIn("if command == \"/setapplications\":", patched)
        self.assertLess(patched.index('if command in ("/birthday"'),
                        patched.index('if chat.get("type")'))
        subprocess.run([sys.executable, str(PATCH), str(target)], check=True,
                       capture_output=True, text=True)
        self.assertEqual(patched, target.read_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)
