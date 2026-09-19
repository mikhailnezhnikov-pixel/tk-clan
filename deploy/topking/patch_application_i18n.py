from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text()
MARKER = "TELEGRAM_APPLICATION_I18N_V1"
if MARKER in s:
    print("TELEGRAM_APPLICATION_I18N_ALREADY_PRESENT")
    raise SystemExit(0)

old_fields = '''APPLICATION_FIELDS = (
    ("power", "Укажите вашу силу в игре."),
    ("influence", "Укажите ваше влияние."),
    ("country", "Укажите страну."),
    ("timezone", "Укажите часовой пояс, например UTC+9."),
    ("branches", "Укажите уровни прокачки веток для клана."),
    ("game_online", "Сколько времени вы онлайн в игре?"),
    ("chat_online", "Как часто вы онлайн в чатах?"),
)
FEEDBACK_TYPES = {"wish": "Пожелание", "suggestion": "Предложение", "question": "Вопрос"}
'''
new_fields = '''# TELEGRAM_APPLICATION_I18N_V1
APPLICATION_FIELDS = (
    ("power", "Сила", "Укажите вашу силу в игре."),
    ("influence", "Влияние", "Укажите ваше влияние."),
    ("country", "Страна", "Укажите страну."),
    ("timezone", "Часовой пояс", "Укажите часовой пояс, например UTC+9."),
    ("branches", "Прокачка веток", "Укажите уровни прокачки веток для клана."),
    ("game_online", "Онлайн в игре", "Сколько времени вы онлайн в игре?"),
    ("chat_online", "Онлайн в чатах", "Как часто вы онлайн в чатах?"),
    ("goals", "Цели", "Каковы ваши цели в игре и в клане?"),
    ("reason", "Причина перехода", "Почему вы хотите перейти именно в Top King?"),
    ("expectations", "Ожидания от клана", "Что вы ждёте от клана Top King?"),
    ("about", "От себя", "Что хотите добавить от себя?\\n\\nЭто необязательный вопрос — отправьте /skip, чтобы пропустить."),
)
APPLICATION_FIELDS_EN = (
    ("power", "Power", "Enter your power in the game."),
    ("influence", "Influence", "Enter your influence."),
    ("country", "Country", "What country are you from?"),
    ("timezone", "Time zone", "Enter your time zone, for example UTC+9."),
    ("branches", "Clan branch levels", "Enter your clan branch progression levels."),
    ("game_online", "In-game activity", "How much time are you online in the game?"),
    ("chat_online", "Chat activity", "How often are you online in clan chats?"),
    ("goals", "Goals", "What are your goals in the game and in a clan?"),
    ("reason", "Reason for joining", "Why do you want to join Top King?"),
    ("expectations", "Expectations", "What do you expect from Top King?"),
    ("about", "Anything else", "Anything else you would like to add?\\n\\nThis question is optional — send /skip to skip it."),
)
APPLICATION_OPTIONAL_FIELDS = frozenset({"about"})
FEEDBACK_TYPES = {"wish": "Пожелание", "suggestion": "Предложение", "question": "Вопрос"}


def application_language(state: dict | None) -> str:
    if not state or not isinstance(state.get("data"), dict):
        return "ru"
    return "en" if state["data"].get("lang") == "en" else "ru"


def application_fields(state: dict | None) -> tuple:
    return APPLICATION_FIELDS_EN if application_language(state) == "en" else APPLICATION_FIELDS


def application_message(state: dict | None, key: str) -> str:
    lang = application_language(state)
    messages = {
        "ru": {
            "choose_language": "Выберите язык анкеты / Choose application language:",
            "help": "/cancel — отменить, /back — вернуться назад, /language — сменить язык",
            "send": "Отправить?",
            "submit": "✅ Отправить",
            "edit": "✏️ Исправить",
            "cancel": "❌ Отмена",
            "cancelled": "Диалог отменён.",
            "edit_prompt": "Введите исправленный ответ.",
            "sent": "✅ Заявка отправлена администраторам Top King.",
            "failed": "Не удалось отправить заявку. Попробуйте позже.",
            "not_configured": "Сервис временно не настроен. Попробуйте позже.",
            "rate": "Заявка уже отправлена. Следующую отправку можно сделать через 5 минут.",
            "title": "Заявка в клан Top King",
            "from": "От",
        },
        "en": {
            "choose_language": "Choose application language / Выберите язык анкеты:",
            "help": "/cancel — cancel, /back — go back, /language — change language",
            "send": "Submit application?",
            "submit": "✅ Submit",
            "edit": "✏️ Edit",
            "cancel": "❌ Cancel",
            "cancelled": "Application cancelled.",
            "edit_prompt": "Enter the corrected answer.",
            "sent": "✅ Your application has been sent to the Top King admins.",
            "failed": "Could not send the application. Please try again later.",
            "not_configured": "The service is temporarily unavailable. Please try again later.",
            "rate": "Your application was already sent. You can submit another one in 5 minutes.",
            "title": "Top King clan application",
            "from": "From",
        },
    }
    return messages[lang][key]


def telegram_application_language_buttons() -> list[list[tuple[str, str]]]:
    return [[("🇷🇺 Русский", "app-lang:ru"), ("🇬🇧 English", "app-lang:en")]]


def telegram_application_prompt(state: dict) -> str:
    fields = application_fields(state)
    if state["step"] < 0:
        return application_message(state, "choose_language")
    step = min(max(0, state["step"]), len(fields) - 1)
    return fields[step][2]
'''
if old_fields not in s:
    raise SystemExit("application fields anchor missing")
s = s.replace(old_fields, new_fields, 1)

old_summary = '''def telegram_summary(state: dict) -> str:
    data = state["data"]
    if state["scenario"] == "feedback":
        return ("<b>Обратная связь</b>\\n"
                f"Тип: {html.escape(FEEDBACK_TYPES.get(data.get('type'), '—'))}\\n"
                f"Текст: {html.escape(str(data.get('text', '—')))}")
    labels = {key: prompt.removesuffix(".") for key, prompt in APPLICATION_FIELDS}
    lines = ["<b>Заявка в клан Top King</b>"]
    for key, _ in APPLICATION_FIELDS:
        lines.append(f"{html.escape(labels[key])}: {html.escape(str(data.get(key, '—')))}")
    return "\\n".join(lines)


def telegram_confirm(state: dict) -> None:
    telegram_send(state["chat_id"], telegram_summary(state) + "\\n\\nОтправить?", [
        [("✅ Отправить", "submit:yes"), ("✏️ Исправить", "submit:edit")],
        [("❌ Отмена", "submit:cancel")],
    ])


def start_telegram_flow(telegram_id: str, chat_id: str, scenario: str) -> None:
    if scenario == "feedback":
        save_telegram_state(telegram_id, chat_id, scenario, 0, {})
        telegram_send(chat_id, "Выберите тип обращения:", [[
            ("Пожелание", "feedback:wish"), ("Предложение", "feedback:suggestion"),
            ("Вопрос", "feedback:question")]])
    else:
        save_telegram_state(telegram_id, chat_id, "application", 0, {})
        telegram_send(chat_id, APPLICATION_FIELDS[0][1] + "\\n\\n/cancel — отменить, /back — вернуться назад")
'''
new_summary = '''def telegram_summary(state: dict) -> str:
    data = state["data"]
    if state["scenario"] == "feedback":
        return ("<b>Обратная связь</b>\\n"
                f"Тип: {html.escape(FEEDBACK_TYPES.get(data.get('type'), '—'))}\\n"
                f"Текст: {html.escape(str(data.get('text', '—')))}")
    fields = application_fields(state)
    lines = [f"<b>{html.escape(application_message(state, 'title'))}</b>"]
    for key, label, _prompt in fields:
        value = data.get(key)
        if key in APPLICATION_OPTIONAL_FIELDS and not value:
            value = "—"
        lines.append(f"{html.escape(label)}: {html.escape(str(value or '—'))}")
    return "\\n".join(lines)


def telegram_confirm(state: dict) -> None:
    if state["scenario"] == "application":
        question = application_message(state, "send")
        buttons = [
            [(application_message(state, "submit"), "submit:yes"),
             (application_message(state, "edit"), "submit:edit")],
            [(application_message(state, "cancel"), "submit:cancel")],
        ]
        telegram_send(state["chat_id"], telegram_summary(state) + "\\n\\n" + question, buttons)
        return
    telegram_send(state["chat_id"], telegram_summary(state) + "\\n\\nОтправить?", [
        [("✅ Отправить", "submit:yes"), ("✏️ Исправить", "submit:edit")],
        [("❌ Отмена", "submit:cancel")],
    ])


def start_telegram_flow(telegram_id: str, chat_id: str, scenario: str) -> None:
    if scenario == "feedback":
        save_telegram_state(telegram_id, chat_id, scenario, 0, {})
        telegram_send(chat_id, "Выберите тип обращения:", [[
            ("Пожелание", "feedback:wish"), ("Предложение", "feedback:suggestion"),
            ("Вопрос", "feedback:question")]])
    else:
        save_telegram_state(telegram_id, chat_id, "application", -1, {})
        state = telegram_state(telegram_id)
        telegram_send(chat_id, application_message(state, "choose_language"),
                      telegram_application_language_buttons())
'''
if old_summary not in s:
    raise SystemExit("summary/start flow anchor missing")
s = s.replace(old_summary, new_summary, 1)

old_submit_intro = '''def submit_telegram_flow(state: dict, user: dict) -> None:
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
'''
new_submit_intro = '''def submit_telegram_flow(state: dict, user: dict) -> None:
    telegram_id, chat_id = state["telegram_id"], state["chat_id"]
    application_target = telegram_delivery_target("application") if state["scenario"] == "application" else None
    target_chat_id = application_target["chat_id"] if application_target else TELEGRAM_ADMIN_CHAT_ID
    target_thread_id = application_target["thread_id"] if application_target else None
    if not target_chat_id:
        telegram_send(chat_id, application_message(state, "not_configured")
                      if state["scenario"] == "application" else "Сервис временно не настроен. Попробуйте позже.")
        return
    if not rate_allowed(f"telegram-submit:{telegram_id}", 1, 300):
        telegram_send(chat_id, application_message(state, "rate")
                      if state["scenario"] == "application"
                      else "Сообщение уже отправлено. Следующую отправку можно сделать через 5 минут.")
        return
'''
if old_submit_intro not in s:
    raise SystemExit("submit intro anchor missing")
s = s.replace(old_submit_intro, new_submit_intro, 1)

old_card = '''    card = telegram_summary(state) + f"\\n\\nОт: {html.escape(sender)}\\nTelegram ID: <code>{html.escape(telegram_id)}</code>"
'''
new_card = '''    sender_label = application_message(state, "from") if state["scenario"] == "application" else "От"
    card = telegram_summary(state) + f"\\n\\n{html.escape(sender_label)}: {html.escape(sender)}\\nTelegram ID: <code>{html.escape(telegram_id)}</code>"
'''
if old_card not in s:
    raise SystemExit("card sender anchor missing")
s = s.replace(old_card, new_card, 1)

old_result = '''    if delivered:
        clear_telegram_state(telegram_id)
        telegram_send(chat_id, "✅ Отправлено администраторам Top King.")
    else:
        telegram_send(chat_id, "Не удалось отправить. Попробуйте позже.")
'''
new_result = '''    if delivered:
        clear_telegram_state(telegram_id)
        telegram_send(chat_id, application_message(state, "sent")
                      if state["scenario"] == "application"
                      else "✅ Отправлено администраторам Top King.")
    else:
        telegram_send(chat_id, application_message(state, "failed")
                      if state["scenario"] == "application"
                      else "Не удалось отправить. Попробуйте позже.")
'''
if old_result not in s:
    raise SystemExit("submit result anchor missing")
s = s.replace(old_result, new_result, 1)

old_cancel = '''    if text == "/cancel" or callback_data == "submit:cancel":
        clear_telegram_state(telegram_id); telegram_send(chat_id, "Диалог отменён."); return
    state = telegram_state(telegram_id)
'''
new_cancel = '''    if text == "/cancel" or callback_data == "submit:cancel":
        current_state = telegram_state(telegram_id)
        cancelled = (application_message(current_state, "cancelled")
                     if current_state and current_state["scenario"] == "application"
                     else "Диалог отменён.")
        clear_telegram_state(telegram_id)
        telegram_send(chat_id, cancelled)
        return
    state = telegram_state(telegram_id)
'''
if old_cancel not in s:
    raise SystemExit("cancel anchor missing")
s = s.replace(old_cancel, new_cancel, 1)

old_feedback_callback = '''    if callback_data.startswith("feedback:") and state["scenario"] == "feedback":
        kind = callback_data.partition(":")[2]
        if kind in FEEDBACK_TYPES:
            state["data"]["type"] = kind
            save_telegram_state(telegram_id, chat_id, "feedback", 1, state["data"])
            telegram_send(chat_id, "Напишите текст обращения.")
        return
    if callback_data == "submit:yes":
'''
new_feedback_callback = '''    if callback_data.startswith("feedback:") and state["scenario"] == "feedback":
        kind = callback_data.partition(":")[2]
        if kind in FEEDBACK_TYPES:
            state["data"]["type"] = kind
            save_telegram_state(telegram_id, chat_id, "feedback", 1, state["data"])
            telegram_send(chat_id, "Напишите текст обращения.")
        return
    if callback_data.startswith("app-lang:") and state["scenario"] == "application":
        lang = callback_data.partition(":")[2]
        if lang not in ("ru", "en"):
            return
        state["data"]["lang"] = lang
        next_step = 0 if state["step"] < 0 else state["step"]
        save_telegram_state(telegram_id, chat_id, "application", next_step, state["data"])
        state = telegram_state(telegram_id)
        telegram_send(chat_id, telegram_application_prompt(state) + "\\n\\n" + application_message(state, "help"))
        return
    if text == "/language" and state["scenario"] == "application":
        telegram_send(chat_id, application_message(state, "choose_language"),
                      telegram_application_language_buttons())
        return
    if callback_data == "submit:yes":
'''
if old_feedback_callback not in s:
    raise SystemExit("language callback anchor missing")
s = s.replace(old_feedback_callback, new_feedback_callback, 1)

old_edit_back = '''    if callback_data == "submit:edit":
        step = 1 if state["scenario"] == "feedback" else 0
        save_telegram_state(telegram_id, chat_id, state["scenario"], step, state["data"])
        telegram_send(chat_id, "Введите исправленный текст." if state["scenario"] == "feedback" else APPLICATION_FIELDS[0][1])
        return
    if text == "/back":
        step = max(0, state["step"] - 1)
        save_telegram_state(telegram_id, chat_id, state["scenario"], step, state["data"])
        prompt = "Напишите текст обращения." if state["scenario"] == "feedback" else APPLICATION_FIELDS[step][1]
        telegram_send(chat_id, prompt); return
'''
new_edit_back = '''    if callback_data == "submit:edit":
        step = 1 if state["scenario"] == "feedback" else 0
        save_telegram_state(telegram_id, chat_id, state["scenario"], step, state["data"])
        if state["scenario"] == "feedback":
            telegram_send(chat_id, "Введите исправленный текст.")
        else:
            state = telegram_state(telegram_id)
            telegram_send(chat_id, telegram_application_prompt(state) + "\\n\\n" + application_message(state, "help"))
        return
    if text == "/back":
        if state["scenario"] == "feedback":
            step = max(0, state["step"] - 1)
            save_telegram_state(telegram_id, chat_id, "feedback", step, state["data"])
            telegram_send(chat_id, "Напишите текст обращения.")
            return
        if state["step"] <= 0:
            save_telegram_state(telegram_id, chat_id, "application", -1, state["data"])
            state = telegram_state(telegram_id)
            telegram_send(chat_id, application_message(state, "choose_language"),
                          telegram_application_language_buttons())
            return
        step = state["step"] - 1
        save_telegram_state(telegram_id, chat_id, "application", step, state["data"])
        state = telegram_state(telegram_id)
        telegram_send(chat_id, telegram_application_prompt(state) + "\\n\\n" + application_message(state, "help"))
        return
'''
if old_edit_back not in s:
    raise SystemExit("edit/back anchor missing")
s = s.replace(old_edit_back, new_edit_back, 1)

old_application_tail = '''    step = min(state["step"], len(APPLICATION_FIELDS) - 1)
    field, _prompt = APPLICATION_FIELDS[step]
    state["data"][field] = text
    if step + 1 < len(APPLICATION_FIELDS):
        save_telegram_state(telegram_id, chat_id, "application", step + 1, state["data"])
        telegram_send(chat_id, APPLICATION_FIELDS[step + 1][1])
    else:
        save_telegram_state(telegram_id, chat_id, "application", len(APPLICATION_FIELDS), state["data"])
        telegram_confirm(telegram_state(telegram_id))
'''
new_application_tail = '''    if state["step"] < 0 or state["data"].get("lang") not in ("ru", "en"):
        telegram_send(chat_id, application_message(state, "choose_language"),
                      telegram_application_language_buttons())
        return
    fields = application_fields(state)
    step = min(state["step"], len(fields) - 1)
    field, _label, _prompt = fields[step]
    if text == "/skip":
        if field not in APPLICATION_OPTIONAL_FIELDS:
            return
        state["data"][field] = ""
    else:
        state["data"][field] = text
    if step + 1 < len(fields):
        save_telegram_state(telegram_id, chat_id, "application", step + 1, state["data"])
        state = telegram_state(telegram_id)
        telegram_send(chat_id, telegram_application_prompt(state) + "\\n\\n" + application_message(state, "help"))
    else:
        save_telegram_state(telegram_id, chat_id, "application", len(fields), state["data"])
        telegram_confirm(telegram_state(telegram_id))
'''
if old_application_tail not in s:
    raise SystemExit("application tail anchor missing")
s = s.replace(old_application_tail, new_application_tail, 1)

path.write_text(s)
print("TELEGRAM_APPLICATION_I18N_PATCH_OK")
