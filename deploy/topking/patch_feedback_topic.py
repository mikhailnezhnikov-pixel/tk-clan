from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text()
MARKER = "TELEGRAM_FEEDBACK_TOPIC_V1"
if MARKER in s:
    print("TELEGRAM_FEEDBACK_TOPIC_ALREADY_PRESENT")
    raise SystemExit(0)

old_target = '''    application_target = telegram_delivery_target("application") if state["scenario"] == "application" else None
    target_chat_id = application_target["chat_id"] if application_target else TELEGRAM_ADMIN_CHAT_ID
    target_thread_id = application_target["thread_id"] if application_target else None
'''
new_target = '''    # TELEGRAM_FEEDBACK_TOPIC_V1
    delivery_kind = "application" if state["scenario"] == "application" else "feedback"
    delivery_target = telegram_delivery_target(delivery_kind)
    target_chat_id = delivery_target["chat_id"] if delivery_target else TELEGRAM_ADMIN_CHAT_ID
    target_thread_id = delivery_target["thread_id"] if delivery_target else None
'''
if old_target not in s:
    raise SystemExit("delivery target anchor missing")
s = s.replace(old_target, new_target, 1)

old_fallback = '''    if (not delivered and state["scenario"] == "application"
            and TELEGRAM_ADMIN_CHAT_ID and target_chat_id != TELEGRAM_ADMIN_CHAT_ID):
        delivered = telegram_send(TELEGRAM_ADMIN_CHAT_ID, card)
'''
new_fallback = '''    if (not delivered and TELEGRAM_ADMIN_CHAT_ID
            and target_chat_id != TELEGRAM_ADMIN_CHAT_ID):
        delivered = telegram_send(TELEGRAM_ADMIN_CHAT_ID, card)
'''
if old_fallback not in s:
    raise SystemExit("delivery fallback anchor missing")
s = s.replace(old_fallback, new_fallback, 1)

anchor = '''        return

    # TELEGRAM_GROUP_SILENCE_V2
'''
feedback_block = '''        return

    if command == "/setfeedback":
        if not telegram_can_configure_delivery(telegram_id):
            telegram_send(chat_id, "⛔ Недостаточно прав для настройки темы обратной связи.",
                          message_thread_id=message.get("message_thread_id"))
            return
        thread_id = message.get("message_thread_id")
        if chat.get("type") != "supergroup" or thread_id is None:
            telegram_send(chat_id,
                          "Откройте нужную тему группы и отправьте /setfeedback прямо внутри этой темы.")
            return
        save_telegram_delivery_target("feedback", chat_id, int(thread_id), telegram_id)
        telegram_send(chat_id,
                      "✅ Эта тема назначена для обратной связи Top King.",
                      message_thread_id=int(thread_id))
        return

    # TELEGRAM_GROUP_SILENCE_V2
'''
if anchor not in s:
    raise SystemExit("feedback command anchor missing")
s = s.replace(anchor, feedback_block, 1)

path.write_text(s)
print("TELEGRAM_FEEDBACK_TOPIC_PATCH_OK")
