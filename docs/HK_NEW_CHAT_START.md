# HK / Top King — START HERE IN A NEW CHAT

## Главное правило

Не восстанавливать существующую механику HK по памяти, описанию в чате, скриншотам или roadmap.

Для задач по переносу/копированию механики сначала нужен **DONOR / REFERENCE SCRIPT** — внешний исходник, с которого мы копируем данные, API-вызовы и поведение.

## Перед работой открыть

1. `reference/topking/README.md`
2. точный donor/reference script из `reference/topking/` — если он уже сохранён
3. `baseline/topking/BASELINE.json`
4. `baseline/topking/HamsterKingMobile.current.user.js`
5. `docs/HK_MASTER_ROADMAP.md` — только для текущего этапа

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

> Работай по `docs/HK_NEW_CHAT_START.md`. Для переносимой механики сначала используй точный donor/reference script из `reference/topking/`, а наш `baseline/topking/HamsterKingMobile.current.user.js` используй только как текущую реализацию для интеграции. Не придумывай механику по тексту. Затем выполняй указанный этап из `docs/HK_MASTER_ROADMAP.md`.
