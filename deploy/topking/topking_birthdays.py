"""Birthday commands and Yakutsk 09:00 greetings for the existing Top King bot.

Uses the host's telegram_send() function. Never starts a second Telegram bot.
"""
# TOPKING_BIRTHDAYS_V1
from datetime import date, datetime, time
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo
import logging
import random
import re
import sqlite3
import threading
import time as clock

YAKUTSK = ZoneInfo("Asia/Yakutsk")
DB_FILE = Path(__file__).with_name("birthdays.sqlite3")
LOG = logging.getLogger("topking.birthdays")
_COMMANDS = frozenset(("/birthday", "/mybirthday", "/birthdays",
                       "/deletebirthday", "/birthdayhelp"))
_MESSAGES = (
    "🎂 Пусть удача, счастье и большие победы сопровождают тебя весь год! 🏆",
    "🎉 Желаем здоровья, море улыбок и приятных сюрпризов! ❤️",
    "🥳 Пусть желания исполняются, а настроение всегда будет на высоте! 🎁",
    "🎈 Пусть жизнь будет ярче праздничного салюта, а побед будет ещё больше! 😄",
    "👑 Пусть твоя корона не падает, а удача никогда не заканчивается! 🎂",
    "🎁 Желаем верных друзей, открытий и множества поводов улыбаться! ✨",
    "🔥 Новый уровень открыт: +100 к счастью и +1000 к удаче! 🎮",
    "🌟 Пусть мечты становятся планами, а планы — реальностью! 🎉",
)
_started = False
_start_lock = threading.Lock()


def _connect():
    conn = sqlite3.connect(str(DB_FILE), timeout=30)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""CREATE TABLE IF NOT EXISTS topking_birthdays (
        chat_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        display_name TEXT NOT NULL,
        day INTEGER NOT NULL,
        month INTEGER NOT NULL,
        PRIMARY KEY (chat_id, user_id))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS topking_birthday_deliveries (
        chat_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        year INTEGER NOT NULL,
        state TEXT NOT NULL,
        claimed_at INTEGER NOT NULL,
        sent_at INTEGER,
        PRIMARY KEY (chat_id, user_id, year))""")
    conn.commit()
    return conn


def _parse_date(value):
    match = re.fullmatch(r"(\d{1,2})\.(\d{1,2})", str(value).strip())
    if not match:
        raise ValueError("format")
    day, month = map(int, match.groups())
    date(2000, month, day)  # 29 February is valid in leap years.
    return day, month


def _next_occurrence(day, month, today):
    for year in range(today.year, today.year + 9):
        try:
            candidate = date(year, month, day)
        except ValueError:
            continue
        if candidate >= today:
            return candidate
    raise ValueError("invalid birthday")


def _safe_name(user):
    value = str(user.get("first_name") or "").strip()
    last = str(user.get("last_name") or "").strip()
    if last:
        value = (value + " " + last).strip()
    if not value:
        value = str(user.get("username") or "Участник")
    return value[:120]


def handle_command(command, text, chat, user, send, message_thread_id=None):
    """Return True only for our commands; other handlers are untouched."""
    command = str(command or "").lower().split("@", 1)[0]
    if command not in _COMMANDS:
        return False
    chat_id = chat.get("id")
    user_id = user.get("id")
    if chat_id is None or user_id is None:
        return True
    chat_id, user_id = int(chat_id), int(user_id)

    def reply(message):
        # Existing telegram_send accepts optional message_thread_id.
        return send(str(chat_id), message, message_thread_id=message_thread_id)

    if chat.get("type") not in ("group", "supergroup"):
        reply("🎂 Команды дней рождения работают в группе клана.")
        return True

    if command == "/birthdayhelp":
        reply("🎂 <b>Дни рождения Top King</b>\n"
              "/birthday ДД.ММ — добавить или изменить свою дату\n"
              "/mybirthday — моя дата\n"
              "/birthdays — полный список дней рождения\n"
              "/deletebirthday — удалить свою дату\n\n"
              "Поздравления — в 09:00 по Якутску. "
              "29 февраля поздравляем только в високосный год.")
        return True

    if command == "/birthday":
        parts = str(text or "").strip().split()
        if len(parts) != 2:
            reply("Укажи дату: /birthday 02.10")
            return True
        try:
            day, month = _parse_date(parts[1])
        except (ValueError, TypeError):
            reply("Неверная дата. Пример: /birthday 02.10")
            return True
        name = _safe_name(user)
        with _connect() as db:
            db.execute("""INSERT INTO topking_birthdays
                          (chat_id,user_id,display_name,day,month) VALUES(?,?,?,?,?)
                          ON CONFLICT(chat_id,user_id) DO UPDATE SET
                          display_name=excluded.display_name,
                          day=excluded.day,month=excluded.month""",
                       (chat_id, user_id, name, day, month))
        reply(f"✅ {escape(name)}, твой день рождения {day:02d}.{month:02d} сохранён! 🎂")
        return True

    if command == "/mybirthday":
        with _connect() as db:
            row = db.execute("""SELECT day,month FROM topking_birthdays
                                WHERE chat_id=? AND user_id=?""",
                             (chat_id, user_id)).fetchone()
        reply(f"🎂 Твоя дата: {row[0]:02d}.{row[1]:02d}" if row
              else "Дата ещё не сохранена. Используй /birthday 02.10")
        return True

    if command == "/deletebirthday":
        with _connect() as db:
            db.execute("DELETE FROM topking_birthdays WHERE chat_id=? AND user_id=?",
                       (chat_id, user_id))
        # Deliberately retain delivery receipts: delete/re-add cannot send twice.
        reply("🗑 Твоя дата рождения удалена.")
        return True

    if command == "/birthdays":
        today = datetime.now(YAKUTSK).date()
        with _connect() as db:
            rows = db.execute("""SELECT display_name,day,month FROM topking_birthdays
                                 WHERE chat_id=?""", (chat_id,)).fetchall()
        if not rows:
            reply("Пока никто не добавил дату. Начни с /birthday 02.10 🎂")
            return True
        upcoming = sorted((_next_occurrence(day, month, today), name, day, month)
                          for name, day, month in rows)
        header = "🎂 <b>Дни рождения участников Top King:</b>"
        chunks, current = [], header
        for when, name, day, month in upcoming:
            days = (when - today).days
            suffix = " — сегодня! 🎉" if days == 0 else f" — через {days} дн."
            line = f"• {escape(name)} — {day:02d}.{month:02d}{suffix}"
            if len(current) + len(line) + 1 > 3400:
                chunks.append(current)
                current = "🎂 <b>Продолжение списка:</b>"
            current += "\n" + line
        chunks.append(current)
        for chunk in chunks:
            reply(chunk)
        return True
    return False


def _claim(chat_id, user_id, year, timestamp):
    """Claim before sending. An ambiguous crash stays claimed to prevent duplicates."""
    with _connect() as db:
        cur = db.execute("""INSERT OR IGNORE INTO topking_birthday_deliveries
                            (chat_id,user_id,year,state,claimed_at)
                            VALUES(?,?,?,'sending',?)""",
                         (chat_id, user_id, year, timestamp))
        return cur.rowcount == 1


def send_due_greetings(send, now=None):
    """Send today's unsent greetings after 09:00 Yakutsk, including after restart."""
    now = now or datetime.now(YAKUTSK)
    if now.tzinfo is None:
        raise ValueError("timezone-aware datetime required")
    now = now.astimezone(YAKUTSK)
    if now.time().replace(tzinfo=None) < time(9, 0):
        return 0
    today = now.date()
    with _connect() as db:
        rows = db.execute("""SELECT chat_id,user_id,display_name FROM topking_birthdays
                             WHERE day=? AND month=? ORDER BY chat_id,user_id""",
                          (today.day, today.month)).fetchall()
    delivered = 0
    for chat_id, user_id, name in rows:
        if not _claim(chat_id, user_id, today.year, int(now.timestamp())):
            continue
        mention = f'<a href="tg://user?id={int(user_id)}">{escape(name)}</a>'
        message = ("🎊 <b>С ДНЁМ РОЖДЕНИЯ!</b> 🎊\n\n" + mention + "!\n\n" +
                   random.choice(_MESSAGES) + "\n\n🎂 С любовью, Top King!")
        success = False
        try:
            success = bool(send(str(chat_id), message))
        except Exception:
            LOG.exception("Birthday greeting delivery failed")
        with _connect() as db:
            if success:
                db.execute("""UPDATE topking_birthday_deliveries
                              SET state='sent',sent_at=?
                              WHERE chat_id=? AND user_id=? AND year=? AND state='sending'""",
                           (int(clock.time()), chat_id, user_id, today.year))
                delivered += 1
            else:
                # Explicit API failure can be retried; ambiguous crash cannot.
                db.execute("""DELETE FROM topking_birthday_deliveries
                              WHERE chat_id=? AND user_id=? AND year=? AND state='sending'""",
                           (chat_id, user_id, today.year))
    return delivered


def start_birthday_scheduler(send):
    """One daemon worker per service process; checks immediately after restart."""
    global _started
    with _start_lock:
        if _started:
            return
        def worker():
            while True:
                try:
                    send_due_greetings(send)
                except Exception:
                    LOG.exception("Birthday scheduler tick failed")
                clock.sleep(45)
        thread = threading.Thread(target=worker, name="topking-birthdays",
                                  daemon=True)
        thread.start()
        _started = True
