from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text()
MARKER = "TELEGRAM_APPLICATION_TOPIC_V1"
if MARKER in s:
    print("TELEGRAM_APPLICATION_TOPIC_ALREADY_PRESENT")
    raise SystemExit(0)

old_send = '''def telegram_send(chat_id: str, text: str, buttons: list[list[tuple[str, str]]] | None = None) -> bool:
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML",
               "disable_web_page_preview": True}
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": [
            [{"text": title, "callback_data": data} for title, data in row] for row in buttons
        ]}
    return telegram_api("sendMessage", payload)
'''
new_send = '''def telegram_send(chat_id: str, text: str, buttons: list[list[tuple[str, str]]] | None = None,
                  message_thread_id: int | None = None) -> bool:
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML",
               "disable_web_page_preview": True}
    if message_thread_id is not None:
        payload["message_thread_id"] = int(message_thread_id)
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": [
            [{"text": title, "callback_data": data} for title, data in row] for row in buttons
        ]}
    return telegram_api("sendMessage", payload)
'''
if old_send not in s:
    raise SystemExit("telegram_send anchor missing")
s = s.replace(old_send, new_send, 1)

old_answer = '''def telegram_answer_callback(callback_id: str) -> None:
    if callback_id:
        telegram_api("answerCallbackQuery", {"callback_query_id": callback_id})


'''
new_answer = '''def telegram_answer_callback(callback_id: str) -> None:
    if callback_id:
        telegram_api("answerCallbackQuery", {"callback_query_id": callback_id})


# TELEGRAM_APPLICATION_TOPIC_V1
def ensure_telegram_delivery_schema() -> None:
    with db_session() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS telegram_delivery_targets (
                      kind TEXT PRIMARY KEY,
                      chat_id TEXT NOT NULL,
                      thread_id INTEGER,
                      updated_by TEXT NOT NULL DEFAULT '',
                      updated_at INTEGER NOT NULL
                    )""")


def telegram_delivery_target(kind: str) -> dict | None:
    ensure_telegram_delivery_schema()
    with db_session() as db:
        row = db.execute("""SELECT chat_id,thread_id,updated_by,updated_at
                            FROM telegram_delivery_targets WHERE kind=?""",
                         (kind,)).fetchone()
    if not row:
        return None
    return {"chat_id": str(row["chat_id"]),
            "thread_id": int(row["thread_id"]) if row["thread_id"] is not None else None,
            "updated_by": str(row["updated_by"] or ""),
            "updated_at": int(row["updated_at"] or 0)}


def save_telegram_delivery_target(kind: str, chat_id: str, thread_id: int | None, updated_by: str) -> None:
    ensure_telegram_delivery_schema()
    with db_session() as db:
        db.execute("""INSERT INTO telegram_delivery_targets(kind,chat_id,thread_id,updated_by,updated_at)
                      VALUES(?,?,?,?,?)
                      ON CONFLICT(kind) DO UPDATE SET
                      chat_id=excluded.chat_id,
                      thread_id=excluded.thread_id,
                      updated_by=excluded.updated_by,
                      updated_at=excluded.updated_at""",
                   (kind, str(chat_id), int(thread_id) if thread_id is not None else None,
                    str(updated_by), utc_now()))


def telegram_can_configure_delivery(telegram_id: str) -> bool:
    if TELEGRAM_ADMIN_CHAT_ID and telegram_id == TELEGRAM_ADMIN_CHAT_ID:
        return True
    with db_session() as db:
        row = db.execute("""SELECT active,maps_manage FROM clan_members
                            WHERE telegram_id=?""", (telegram_id,)).fetchone()
    return bool(row and row["active"] and row["maps_manage"])


'''
if old_answer not in s:
    raise SystemExit("callback helper anchor missing")
s = s.replace(old_answer, new_answer, 1)

old_submit = '''def submit_telegram_flow(state: dict, user: dict) -> None:
    telegram_id, chat_id = state["telegram_id"], state["chat_id"]
    if not TELEGRAM_ADMIN_CHAT_ID:
        telegram_send(chat_id, "Сервис временно не настроен. Попробуйте позже.")
        return
    if not rate_allowed(f"telegram-submit:{telegram_id}", 1, 300):
        telegram_send(chat_id, "Сообщение уже отправлено. Следующую отправку можно сделать через 5 минут.")
        return
    username = clean_public_name(user.get("username"), 64)
    sender = f"@{username}" if username else clean_public_name(user.get("first_name"), 64) or telegram_id
    card = telegram_summary(state) + f"\\n\\nОт: {html.escape(sender)}\\nTelegram ID: <code>{html.escape(telegram_id)}</code>"
    if telegram_send(TELEGRAM_ADMIN_CHAT_ID, card):
        clear_telegram_state(telegram_id)
        telegram_send(chat_id, "✅ Отправлено администраторам Top King.")
    else:
        telegram_send(chat_id, "Не удалось отправить. Попробуйте позже.")
'''
new_submit = '''def submit_telegram_flow(state: dict, user: dict) -> None:
    telegram_id, chat_id = state["telegram_id"], state["chat_id"]
    application_target = telegram_delivery_target("application") if state["scenario"] == "application" else None
    target_chat_id = application_target["chat_id"] if application_target else TELEGRAM_ADMIN_CHAT_ID
    target_thread_id = application_target["thread_id"] if application_target else None
    if not target_chat_id:
        telegram_send(chat_id, "Сервис временно не настроен. Попробуйте позже.")
        return
    if not rate_allowed(f"telegram-submit:{telegram_id}", 1, 300):
        telegram_send(chat_id, "Сообщение уже отправлено. Следующую отправку можно сделать через 5 минут.")
        return
    username = clean_public_name(user.get("username"), 64)
    sender = f"@{username}" if username else clean_public_name(user.get("first_name"), 64) or telegram_id
    card = telegram_summary(state) + f"\\n\\nОт: {html.escape(sender)}\\nTelegram ID: <code>{html.escape(telegram_id)}</code>"

    delivered = telegram_send(target_chat_id, card, message_thread_id=target_thread_id)
    # If the configured topic was removed or the bot lost topic access,
    # keep the application from being lost by falling back to the owner chat.
    if (not delivered and state["scenario"] == "application"
            and TELEGRAM_ADMIN_CHAT_ID and target_chat_id != TELEGRAM_ADMIN_CHAT_ID):
        delivered = telegram_send(TELEGRAM_ADMIN_CHAT_ID, card)

    if delivered:
        clear_telegram_state(telegram_id)
        telegram_send(chat_id, "✅ Отправлено администраторам Top King.")
    else:
        telegram_send(chat_id, "Не удалось отправить. Попробуйте позже.")
'''
if old_submit not in s:
    raise SystemExit("submit flow anchor missing")
s = s.replace(old_submit, new_submit, 1)

old_context = '''    telegram_id, chat_id = str(user.get("id", "")), str((message.get("chat") or {}).get("id", ""))
    if not TELEGRAM_ID_RE.fullmatch(telegram_id) or not chat_id:
        return
    if not rate_allowed(f"telegram-update:{telegram_id}", 30, 60):
        return
    callback_data = clean_public_name((callback or {}).get("data"), 64)
    if callback:
        telegram_answer_callback(str(callback.get("id", "")))
    text = clean_public_name(message.get("text"), 2000)
    if text.startswith("/start"):
'''
new_context = '''    chat = message.get("chat") or {}
    telegram_id, chat_id = str(user.get("id", "")), str(chat.get("id", ""))
    if not TELEGRAM_ID_RE.fullmatch(telegram_id) or not chat_id:
        return
    if not rate_allowed(f"telegram-update:{telegram_id}", 30, 60):
        return
    callback_data = clean_public_name((callback or {}).get("data"), 64)
    if callback:
        telegram_answer_callback(str(callback.get("id", "")))
    text = clean_public_name(message.get("text"), 2000)

    command = text.split(None, 1)[0].lower() if text.startswith("/") else ""
    command = command.split("@", 1)[0]
    if command == "/setapplications":
        if not telegram_can_configure_delivery(telegram_id):
            telegram_send(chat_id, "⛔ Недостаточно прав для настройки темы заявок.",
                          message_thread_id=message.get("message_thread_id"))
            return
        thread_id = message.get("message_thread_id")
        if chat.get("type") != "supergroup" or thread_id is None:
            telegram_send(chat_id,
                          "Откройте в группе тему «Заявки» и отправьте эту команду прямо внутри темы.")
            return
        save_telegram_delivery_target("application", chat_id, int(thread_id), telegram_id)
        telegram_send(chat_id,
                      "✅ Эта тема назначена для новых заявок в клан Top King.",
                      message_thread_id=int(thread_id))
        return

    if text.startswith("/start"):
'''
if old_context not in s:
    raise SystemExit("telegram update context anchor missing")
s = s.replace(old_context, new_context, 1)

path.write_text(s)
print("TELEGRAM_APPLICATION_TOPIC_PATCH_OK")
