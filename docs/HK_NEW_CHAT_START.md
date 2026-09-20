# HK / Top King — START HERE IN A NEW CHAT

## Главное правило

Не восстанавливать существующую механику HK по памяти, описанию в чате, скриншотам или roadmap.

Для задач по переносу/копированию механики сначала нужен **DONOR / REFERENCE SCRIPT** — внешний исходник, с которого мы копируем данные, API-вызовы и поведение.

## Перед работой открыть

### Автоматический SOURCE PREFLIGHT

Если пользователь пишет **«начни этап N»** или **«продолжи этап N»**, сначала обязательно:

1. открыть `reference/topking/REFERENCE.json`;
2. найти указанный там pinned donor в ChatGPT File Library;
3. сверить donor по версии/source anchors;
4. прочитать относящийся к этапу donor-код;
5. открыть `baseline/topking/BASELINE.json`;
6. открыть `baseline/topking/HamsterKingMobile.current.user.js`;
7. открыть `docs/HK_MASTER_ROADMAP.md` и выполнять только указанный этап.

Текущий pinned donor задаётся **только** `REFERENCE.json`. Живой URL Kokkaras не заменяет закреплённую ревизию.

## Роли источников

### DONOR / REFERENCE

Отвечает на вопрос:

**Как функция должна реально работать?**

Из него берём:

- API endpoints;
- поля ответов;
- порядок запросов;
- расчёты;
- проверки;
- условия;
- механику действий;
- обработку state.

### CURRENT IMPLEMENTATION

`baseline/topking/HamsterKingMobile.current.user.js`

Отвечает на вопрос:

**Как эта механика сейчас встроена в наш HK?**

Он нужен для интеграции и защиты уже работающих частей, но не должен заменять внешний donor-source.

## Приоритет для переносимой функции

1. Точный donor/reference script.
2. Реальные API / definitions игры.
3. Наш текущий implementation baseline.
4. Конкретное ТЗ / roadmap.
5. Контекст и память чата.

## Запрет

Если точный donor-source отсутствует, нельзя выдавать:

- нашу текущую версию;
- старую версию HamsterKingMobile;
- описание из чата;
- предположение по названию функции

за источник истины donor-механики.

Нужно сначала найти или получить точный donor.

## Команда для нового чата

Достаточно написать:

> Начни этап N.

или:

> Продолжи этап N.

Это автоматически означает: выполнить SOURCE PREFLIGHT из `reference/topking/REFERENCE.json`, затем работать только по соответствующему этапу `docs/HK_MASTER_ROADMAP.md`.

Расширенная команда, если нужно явно повторить правило:

> Работай по `docs/HK_NEW_CHAT_START.md`. Сначала выполни SOURCE PREFLIGHT из `reference/topking/REFERENCE.json`, используй pinned donor как источник существующей механики, current baseline — только для интеграции, затем выполняй только указанный этап `docs/HK_MASTER_ROADMAP.md`.
