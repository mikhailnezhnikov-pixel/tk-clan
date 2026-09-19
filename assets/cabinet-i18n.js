(()=>{
  const KEY='tk-language';
  const SUPPORTED=new Set(['ru','en','fa']);

  const EN={
    'Закрытый раздел клана':'Private clan area',
    'Основная навигация':'Main navigation',
    'Меню':'Menu',
    'Загрузка':'Loading',
    'Разделы личного кабинета':'Member area sections',
    'Введите ID из игры':'Enter your game ID',
    'Блоки прокачки':'Progression blocks',
    'Ветки блока':'Block branches',
    'Поиск города или координат, например New York 23:32':'Search by city or coordinates, e.g. New York 23:32',
    'Личный кабинет':'Member area',
    'Доступ к скрипту, статистика участников и актуальная прокачка клана — в одном месте.':'Script access, member statistics and current clan progression — all in one place.',
    'Доступ участника':'Member access',
    'Войти через Telegram':'Sign in with Telegram',
    'Кабинет доступен только Telegram ID, которые разрешены владельцем клана.':'The member area is available only to Telegram IDs approved by the clan owner.',
    'Всё важное — внутри':'Everything important is inside',
    'Скрипт, лицензия и прогресс клана без лишних переходов.':'Script, license and clan progress without unnecessary navigation.',
    'Обзор':'Overview',
    'Статистика игроков':'Player statistics',
    'Карты':'Maps',
    'Покупки на следующую неделю':'Purchases for next week',
    'Список формируется до воскресенья 21:00 по Москве (GMT+3). Значение 0 в публикацию не попадает; заполнять весь лимит не обязательно.':'The list is prepared until Sunday 21:00 Moscow time (GMT+3). Zero values are not published; you do not need to fill the full limit.',
    'Неделя покупок':'Purchase week',
    'Дедлайн':'Deadline',
    'Моя заявка':'My request',
    'До воскресенья 21:00 МСК укажите, сколько вы хотели бы купить. Это пожелание, а не подтверждённая покупка: итог утверждает ответственный.':'Until Sunday 21:00 Moscow time, enter how many items you would like to buy. This is a request, not a confirmed purchase; the final list is approved by the responsible manager.',
    'Заявки игроков':'Player requests',
    'Нажмите «+ Добавить», чтобы перенести запрошенное количество в итоговый список. После этого количество можно изменить вручную ниже.':'Click “+ Add” to copy the requested quantity into the final list. You can then adjust the quantity manually below.',
    'Итоговый список':'Final list',
    'Чтобы оставить заявку, сначала привяжите игровой ID во вкладке «Обзор».':'To submit a request, first link your game ID on the Overview tab.',
    'Ваш игровой ID пока не найден в актуальном составе клана.':'Your game ID is not present in the current clan roster yet.',
    'Приём заявок на эту неделю закрыт. Новый цикл откроется в понедельник.':'Requests for this week are closed. A new cycle opens on Monday.',
    'Заявка сохранена. До дедлайна её можно изменить.':'Request saved. You can change it until the deadline.',
    'Выберите количество — заявка сохранится автоматически.':'Choose a quantity — your request will be saved automatically.',
    'Заявок игроков пока нет.':'There are no player requests yet.',
    '+ Добавить':'+ Add',
    '✓ Добавлено':'✓ Added',
    'Сохраняю вашу заявку…':'Saving your request…',
    'Заявка сохранена.':'Request saved.',
    'Сначала привяжите игровой ID во вкладке «Обзор».':'First link your game ID on the Overview tab.',
    'Приём заявок уже закрыт.':'Requests are already closed.',
    'Не удалось сохранить заявку.':'Could not save the request.',
    'Добавляю заявку в итоговый список…':'Adding request to the final list…',
    'Заявка добавлена в итоговый список.':'Request added to the final list.',
    'Не хватает свободного лимита шаров идолов.':'Not enough idol-orb capacity remains.',
    'Не хватает свободного лимита бизнесов S+.':'Not enough S+ business capacity remains.',
    'Не удалось добавить заявку.':'Could not add the request.',
    'Шары идолов':'Idol orbs',
    'Бизнесы S+':'S+ businesses',
    'Поиск участника':'Search member',
    'Опубликовать':'Publish',
    'Опубликовать обновление':'Publish update',
    'Ещё не опубликовано':'Not published yet',
    'Участник':'Member',
    'Для каждого участника можно поставить от 1 до 3 единиц каждого типа. Ноль означает «не покупать». Общий недельный лимит: 14 шаров идолов и 30 бизнесов S+.':'Each member can receive 1 to 3 units of each type. Zero means no purchase. Weekly limits: 14 idol orbs and 30 S+ businesses.',
    'Участники клана пока не загружены.':'Clan members have not loaded yet.',
    'Загружаю Clan Shop…':'Loading Clan Shop…',
    'Не удалось загрузить Clan Shop.':'Could not load Clan Shop.',
    'Сохраняю…':'Saving…',
    'Сохранено.':'Saved.',
    'Лимит шаров идолов — максимум 14 на неделю.':'Idol orb limit is 14 per week.',
    'Лимит бизнесов S+ — максимум 30 на неделю.':'S+ business limit is 30 per week.',
    'Не удалось сохранить изменение.':'Could not save the change.',
    'Публикую список в Telegram…':'Publishing the list to Telegram…',
    'Список Clan Shop опубликован.':'Clan Shop list published.',
    'Сначала привяжите тему командой /setclanshop@TopKingClanCabinetBot.':'First link the topic with /setclanshop@TopKingClanCabinetBot.',
    'Нечего публиковать: все значения равны 0.':'Nothing to publish: all values are 0.',
    'Telegram не принял сообщение. Проверьте права бота в теме Clan Shop.':'Telegram rejected the message. Check the bot permissions in the Clan Shop topic.',
    'Не удалось опубликовать список.':'Could not publish the list.',
    'Установка':'Installation',
    'Участник клана':'Clan member',
    'Доступ разрешён':'Access granted',
    'Игровой ID':'Game ID',
    'Привязать':'Link',
    'Это нужно сделать один раз. После привязки лицензия скрипта активируется автоматически.':'You only need to do this once. After linking, the script license is activated automatically.',
    'Игровой ID привязан':'Game ID linked',
    'Лицензия уже связана с этим кабинетом. Повторная регистрация не требуется.':'The license is already linked to this account. No repeated registration is required.',
    'Скопировать ID':'Copy ID',
    'Обновить данные':'Refresh data',
    'Выйти':'Sign out',
    'Скрипт':'Script',
    'Актуальная версия':'Current version',
    'Рекомендуемый запуск — через закладку браузера: ничего скачивать и переустанавливать при обновлениях не нужно.':'Recommended launch method: browser bookmark. You do not need to download or reinstall anything when updates are released.',
    'Установить':'Install',
    'Скачать .user.js':'Download .user.js',
    'Прокачка клана':'Clan progression',
    'Последние данные':'Latest data',
    'Участников':'Members',
    'Общий уровень':'Total level',
    'Неделя':'Week',
    'Открыть статистику игроков':'Open player statistics',
    'Клан · статистика':'Clan · statistics',
    'Зеркало вкладки «Клан» из скрипта: общий вклад участников, блоки прокачки, ветки внутри блоков и вклад каждого игрока.':'Mirror of the script’s Clan tab: total member contribution, progression blocks, branches inside each block and each player’s contribution.',
    '▸ Общий вклад участников':'▸ Overall member contribution',
    'Блоки и ветки появятся после того, как сервер передаст полный снимок вкладки «Клан» из скрипта.':'Blocks and branches will appear after the server receives a complete snapshot of the Clan tab from the script.',
    'Ветка':'Branch',
    'Твои уровни':'Your levels',
    'Индекс исследованных районов: здания, события с кристаллами, прогресс исследования и Score. По умолчанию лучшие карты находятся сверху.':'Index of researched districts: buildings, crystal events, research progress and Score. The best maps are shown first by default.',
    'Карт в индексе':'Maps in index',
    'Городов':'Cities',
    'Open подключено':'Open enabled',
    'Доступ пользователей к картам':'User access to maps',
    'Список по умолчанию свернут. Откройте его только когда нужно изменить права.':'The list is collapsed by default. Open it only when you need to change permissions.',
    'Настроить':'Configure',
    'Сначала выберите участника, затем город. Галочка города открывает весь город. Если раскрыть город, можно выдать или снять доступ к каждой карте отдельно. Управляющие картами всегда имеют доступ ко всем картам.':'Select a member first, then a city. Checking a city grants access to the whole city. Expand a city to grant or revoke access to individual maps. Map managers always have access to every map.',
    'Публикация':'Publishing',
    'Нажмите строку карты, чтобы увидеть максимальную награду. Публикация доступна только управляющим картами. После включения карта автоматически появляется в публичном разделе «Карты».':'Select a map row to see the maximum reward. Publishing is available only to map managers. Once enabled, the map automatically appears in the public Maps section.',
    'Установка HK':'HK installation',
    'Запуск через закладку браузера':'Launch with a browser bookmark',
    'Ничего устанавливать в браузер не нужно. Закладка создаётся один раз и при каждом запуске сама загружает актуальную версию HK.':'Nothing needs to be installed in the browser. Create the bookmark once; every launch automatically loads the current HK version.',
    'Создать закладку HK':'Create an HK bookmark',
    '★ Установить HK':'★ Install HK',
    'Скопировать команду':'Copy command',
    'Показать команду вручную':'Show command manually',
    'Адрес закладки должен начинаться с':'The bookmark address must start with',
    'Команда скопирована ✓':'Command copied ✓',
    'Дополнительный скрипт':'Additional script',
    'Kokkaras — слухи и реклама':'Kokkaras — rumors and ads',
    'Автоматизация сбора слухов и рекламы. Устанавливается такой же закладкой в браузере и запускается только на странице Hamster King.':'Automation for collecting rumors and ads. It is installed with the same type of browser bookmark and runs only on the Hamster King page.',
    'Создать закладку Kokkaras':'Create a Kokkaras bookmark',
    'Создайте в этом же браузере отдельную закладку с названием':'Create a separate bookmark in this browser named',
    '. Перетащите кнопку на панель закладок или скопируйте команду и вставьте её в поле':'. Drag the button to the bookmarks bar or copy the command and paste it into the',
    'URL / Адрес':'URL / Address',
    '★ Установить Kokkaras':'★ Install Kokkaras',
    'Команда Kokkaras скопирована ✓':'Kokkaras command copied ✓',
    'Резервный вариант':'Fallback option',
    'Используйте этот вариант только если запуск через закладку не работает в вашем браузере. Файл можно скачать кнопкой':'Use this option only if launching from a bookmark does not work in your browser. Download the file using the',
    '«Скачать .user.js»':'“Download .user.js”',
    'во вкладке «Обзор».':'button on the Overview tab.',
    'Обратная связь':'Feedback',
    'Без города':'No city',
    'В этом городе нет карт.':'There are no maps in this city.',
    'Участник':'Member',
    'управление картами':'map management',
    'все города · все карты':'all cities · all maps',
    'Управляющий картами автоматически имеет доступ ко всем картам. Отдельные разрешения для него не требуются.':'A map manager automatically has access to all maps. No separate permissions are required.',
    'Весь город':'Entire city',
    'Нет участников для настройки.':'No members to configure.',
    'Загружаю закрытый индекс карт…':'Loading private map index…',
    'Не удалось загрузить индекс карт.':'Could not load the map index.',
    'Локальная карта ещё не загружена':'The local map has not been uploaded yet',
    'нет карты':'no map',
    'на сайте':'on site',
    'На сайте':'On site',
    'Закрыта':'Private',
    'Карта опубликована на сайте.':'Map published on the site.',
    'Публикация карты снята.':'Map publication removed.',
    'Сначала должна быть загружена локальная карта.':'The local map must be uploaded first.',
    'Не удалось изменить публикацию.':'Could not change publication status.',
    'Доступ к городу выдан.':'City access granted.',
    'Доступ к городу снят.':'City access revoked.',
    'Не удалось изменить доступ к городу.':'Could not change city access.',
    'Доступ к карте выдан.':'Map access granted.',
    'Доступ к карте снят.':'Map access revoked.',
    'Не удалось изменить доступ к карте.':'Could not change map access.',
    '✓ Скопировано':'✓ Copied',
    'Сессия закончилась. Войдите снова.':'Your session has expired. Sign in again.',
    'Не удалось загрузить кабинет. Попробуйте позже.':'Could not load the member area. Try again later.',
    'Проверяю доступ…':'Checking access…',
    'Этот Telegram ID ещё не разрешён владельцем клана.':'This Telegram ID has not been approved by the clan owner yet.',
    'Не удалось подтвердить вход через Telegram.':'Could not verify Telegram sign-in.',
    'Вход через Telegram пока настраивается.':'Telegram sign-in is still being configured.',
    'Сервер входа временно недоступен.':'The sign-in server is temporarily unavailable.',
    'Введите игровой ID.':'Enter your game ID.',
    'Привязываю игровой ID…':'Linking game ID…',
    'Игровой ID успешно привязан.':'Game ID linked successfully.',
    'Этот игровой ID уже привязан к другому кабинету.':'This game ID is already linked to another account.',
    'Проверьте игровой ID и попробуйте ещё раз.':'Check the game ID and try again.',
    'Готовлю файл…':'Preparing file…',
    'Скрипт загружен.':'Script downloaded.',
    'Не удалось скачать скрипт.':'Could not download the script.',
    'Игровой ID скопирован.':'Game ID copied.',
    'Не удалось скопировать ID.':'Could not copy the ID.',
    'Обновляю данные…':'Refreshing data…',
    'Данные обновлены.':'Data refreshed.',
    'Нет данных по общему вкладу.':'No overall contribution data.',
    'По этой ветке пока нет данных.':'No data for this branch yet.',
    'Сейчас сайт восстанавливает блоки из данных игроков. Для точного зеркала скрипт должен передавать на сервер готовый снимок block → branch → participants.':'The site is currently reconstructing blocks from player data. For an exact mirror, the script must send a ready block → branch → participants snapshot to the server.',
    'Без имени':'Unnamed',
    'Chrome на iPhone не запускает такие javascript-закладки.':'Chrome on iPhone cannot run these JavaScript bookmarks.',
    'Откройте список закладок → Изменить → выберите':'Open bookmarks → Edit → select',
    'Удалите старый адрес и вставьте скопированную команду.':'Delete the old address and paste the copied command.',
    'Замените URL на скопированную команду.':'Replace the URL with the copied command.',
    'Создайте обычную закладку и назовите её':'Create a regular bookmark and name it',
    'Откройте редактирование этой закладки.':'Open this bookmark for editing.',
    'Замените её адрес на скопированную команду и сохраните.':'Replace its address with the copied command and save.',
    'На iPhone Chrome не запускает HK из javascript-закладки. Откройте кабинет и игру в Safari.':'Chrome on iPhone cannot launch HK from a JavaScript bookmark. Open the member area and the game in Safari.',
    'Команда HK уже скопирована. Выполните 4 шага выше.':'The HK command is already copied. Follow the 4 steps above.',
    'Нажмите «Скопировать команду», затем выполните короткую инструкцию.':'Tap “Copy command”, then follow the short instructions.',
    'Chrome на iPhone не поддерживает запуск этой закладки. Используйте Safari.':'Chrome on iPhone does not support launching this bookmark. Use Safari.',
    'Команда HK скопирована. Выполните короткую инструкцию выше.':'HK command copied. Follow the short instructions above.',
    'Не удалось скопировать автоматически. Нажмите «Скопировать команду».':'Automatic copy failed. Tap “Copy command”.',
    'Команда выделена — скопируйте её вручную.':'The command is selected — copy it manually.',
    'Команда Kokkaras скопирована. Выполните короткую инструкцию выше.':'Kokkaras command copied. Follow the short instructions above.'
  };

  const FA={
    'Закрытый раздел клана':'بخش خصوصی قبیله',
    'Основная навигация':'ناوبری اصلی',
    'Меню':'منو',
    'Загрузка':'در حال بارگذاری',
    'Разделы личного кабинета':'بخش‌های پنل اعضا',
    'Введите ID из игры':'شناسه بازی را وارد کنید',
    'Блоки прокачки':'بخش‌های پیشرفت',
    'Ветки блока':'شاخه‌های بخش',
    'Поиск города или координат, например New York 23:32':'جستجو بر اساس شهر یا مختصات، مثلاً New York 23:32',
    'Личный кабинет':'پنل اعضا',
    'Доступ к скрипту, статистика участников и актуальная прокачка клана — в одном месте.':'دسترسی به اسکریپت، آمار اعضا و پیشرفت فعلی قبیله — همه در یک‌جا.',
    'Доступ участника':'دسترسی عضو',
    'Войти через Telegram':'ورود با تلگرام',
    'Кабинет доступен только Telegram ID, которые разрешены владельцем клана.':'پنل فقط برای شناسه‌های تلگرامی که مالک قبیله تأیید کرده در دسترس است.',
    'Всё важное — внутри':'همه چیز مهم اینجاست',
    'Скрипт, лицензия и прогресс клана без лишних переходов.':'اسکریپت، مجوز و پیشرفت قبیله بدون رفت‌وآمد اضافی.',
    'Обзор':'نمای کلی',
    'Статистика игроков':'آمار بازیکنان',
    'Карты':'نقشه‌ها',
    'Покупки на следующую неделю':'خریدهای هفته آینده',
    'Список формируется до воскресенья 21:00 по Москве (GMT+3). Значение 0 в публикацию не попадает; заполнять весь лимит не обязательно.':'فهرست تا یکشنبه ساعت ۲۱:۰۰ به وقت مسکو (GMT+3) آماده می‌شود. مقادیر صفر منتشر نمی‌شوند و پر کردن کل سقف الزامی نیست.',
    'Неделя покупок':'هفته خرید',
    'Дедлайн':'مهلت',
    'Моя заявка':'درخواست من',
    'До воскресенья 21:00 МСК укажите, сколько вы хотели бы купить. Это пожелание, а не подтверждённая покупка: итог утверждает ответственный.':'تا یکشنبه ساعت ۲۱:۰۰ به وقت مسکو تعداد موردنظر خود را وارد کنید. این فقط درخواست است و خرید قطعی محسوب نمی‌شود؛ فهرست نهایی را مسئول تأیید می‌کند.',
    'Заявки игроков':'درخواست‌های بازیکنان',
    'Нажмите «+ Добавить», чтобы перенести запрошенное количество в итоговый список. После этого количество можно изменить вручную ниже.':'برای انتقال تعداد درخواست‌شده به فهرست نهایی روی «+ افزودن» بزنید. سپس می‌توانید مقدار را در پایین به‌صورت دستی تغییر دهید.',
    'Итоговый список':'فهرست نهایی',
    'Чтобы оставить заявку, сначала привяжите игровой ID во вкладке «Обзор».':'برای ثبت درخواست ابتدا شناسه بازی را در تب «نمای کلی» متصل کنید.',
    'Ваш игровой ID пока не найден в актуальном составе клана.':'شناسه بازی شما هنوز در ترکیب فعلی قبیله پیدا نشده است.',
    'Приём заявок на эту неделю закрыт. Новый цикл откроется в понедельник.':'ثبت درخواست‌های این هفته بسته شده است. چرخه جدید دوشنبه باز می‌شود.',
    'Заявка сохранена. До дедлайна её можно изменить.':'درخواست ذخیره شد و تا مهلت قابل تغییر است.',
    'Выберите количество — заявка сохранится автоматически.':'تعداد را انتخاب کنید؛ درخواست خودکار ذخیره می‌شود.',
    'Заявок игроков пока нет.':'هنوز درخواستی از بازیکنان وجود ندارد.',
    '+ Добавить':'+ افزودن',
    '✓ Добавлено':'✓ اضافه شد',
    'Сохраняю вашу заявку…':'در حال ذخیره درخواست شما…',
    'Заявка сохранена.':'درخواست ذخیره شد.',
    'Сначала привяжите игровой ID во вкладке «Обзор».':'ابتدا شناسه بازی را در تب «نمای کلی» متصل کنید.',
    'Приём заявок уже закрыт.':'ثبت درخواست‌ها بسته شده است.',
    'Не удалось сохранить заявку.':'ذخیره درخواست ممکن نشد.',
    'Добавляю заявку в итоговый список…':'در حال افزودن درخواست به فهرست نهایی…',
    'Заявка добавлена в итоговый список.':'درخواست به فهرست نهایی اضافه شد.',
    'Не хватает свободного лимита шаров идолов.':'ظرفیت کافی برای گوی‌های Idol باقی نمانده است.',
    'Не хватает свободного лимита бизнесов S+.':'ظرفیت کافی برای کسب‌وکارهای S+ باقی نمانده است.',
    'Не удалось добавить заявку.':'افزودن درخواست ممکن نشد.',
    'Шары идолов':'گوی‌های Idol',
    'Бизнесы S+':'کسب‌وکارهای S+',
    'Поиск участника':'جستجوی عضو',
    'Опубликовать':'انتشار',
    'Опубликовать обновление':'انتشار به‌روزرسانی',
    'Ещё не опубликовано':'هنوز منتشر نشده',
    'Участник':'عضو',
    'Для каждого участника можно поставить от 1 до 3 единиц каждого типа. Ноль означает «не покупать». Общий недельный лимит: 14 шаров идолов и 30 бизнесов S+.':'برای هر عضو می‌توان ۱ تا ۳ واحد از هر نوع تعیین کرد. صفر یعنی خرید نشود. سقف هفتگی: ۱۴ گوی Idol و ۳۰ کسب‌وکار S+.',
    'Участники клана пока не загружены.':'اعضای قبیله هنوز بارگذاری نشده‌اند.',
    'Загружаю Clan Shop…':'در حال بارگذاری Clan Shop…',
    'Не удалось загрузить Clan Shop.':'بارگذاری Clan Shop ممکن نشد.',
    'Сохраняю…':'در حال ذخیره…',
    'Сохранено.':'ذخیره شد.',
    'Лимит шаров идолов — максимум 14 на неделю.':'حداکثر گوی‌های Idol در هفته ۱۴ است.',
    'Лимит бизнесов S+ — максимум 30 на неделю.':'حداکثر کسب‌وکارهای S+ در هفته ۳۰ است.',
    'Не удалось сохранить изменение.':'ذخیره تغییر ممکن نشد.',
    'Публикую список в Telegram…':'در حال انتشار فهرست در تلگرام…',
    'Список Clan Shop опубликован.':'فهرست Clan Shop منتشر شد.',
    'Сначала привяжите тему командой /setclanshop@TopKingClanCabinetBot.':'ابتدا موضوع را با دستور /setclanshop@TopKingClanCabinetBot متصل کنید.',
    'Нечего публиковать: все значения равны 0.':'چیزی برای انتشار وجود ندارد: همه مقادیر صفر هستند.',
    'Telegram не принял сообщение. Проверьте права бота в теме Clan Shop.':'تلگرام پیام را نپذیرفت. دسترسی ربات در موضوع Clan Shop را بررسی کنید.',
    'Не удалось опубликовать список.':'انتشار فهرست ممکن نشد.',
    'Установка':'نصب',
    'Участник клана':'عضو قبیله',
    'Доступ разрешён':'دسترسی مجاز است',
    'Игровой ID':'شناسه بازی',
    'Привязать':'اتصال',
    'Это нужно сделать один раз. После привязки лицензия скрипта активируется автоматически.':'این کار فقط یک‌بار لازم است. پس از اتصال، مجوز اسکریپت خودکار فعال می‌شود.',
    'Игровой ID привязан':'شناسه بازی متصل شد',
    'Лицензия уже связана с этим кабинетом. Повторная регистрация не требуется.':'مجوز قبلاً به این حساب متصل شده و ثبت دوباره لازم نیست.',
    'Скопировать ID':'کپی شناسه',
    'Обновить данные':'به‌روزرسانی داده‌ها',
    'Выйти':'خروج',
    'Скрипт':'اسکریپت',
    'Актуальная версия':'نسخه فعلی',
    'Рекомендуемый запуск — через закладку браузера: ничего скачивать и переустанавливать при обновлениях не нужно.':'روش پیشنهادی اجرا از طریق نشانک مرورگر است؛ با هر به‌روزرسانی نیازی به دانلود یا نصب دوباره نیست.',
    'Установить':'نصب',
    'Скачать .user.js':'دانلود .user.js',
    'Прокачка клана':'پیشرفت قبیله',
    'Последние данные':'آخرین داده‌ها',
    'Участников':'اعضا',
    'Общий уровень':'سطح کل',
    'Неделя':'هفته',
    'Открыть статистику игроков':'باز کردن آمار بازیکنان',
    'Клан · статистика':'قبیله · آمار',
    'Зеркало вкладки «Клан» из скрипта: общий вклад участников, блоки прокачки, ветки внутри блоков и вклад каждого игрока.':'نمای آینه‌ای تب «قبیله» در اسکریپت: مشارکت کل اعضا، بخش‌های پیشرفت، شاخه‌ها و سهم هر بازیکن.',
    '▸ Общий вклад участников':'▸ مشارکت کل اعضا',
    'Блоки и ветки появятся после того, как сервер передаст полный снимок вкладки «Клан» из скрипта.':'بخش‌ها و شاخه‌ها پس از دریافت تصویر کامل تب «قبیله» از اسکریپت نمایش داده می‌شوند.',
    'Ветка':'شاخه',
    'Твои уровни':'سطح‌های شما',
    'Индекс исследованных районов: здания, события с кристаллами, прогресс исследования и Score. По умолчанию лучшие карты находятся сверху.':'فهرست مناطق بررسی‌شده: ساختمان‌ها، رویدادهای کریستال، پیشرفت بررسی و امتیاز. بهترین نقشه‌ها به‌طور پیش‌فرض بالاتر نمایش داده می‌شوند.',
    'Карт в индексе':'نقشه‌های فهرست',
    'Городов':'شهرها',
    'Open подключено':'Open فعال',
    'Доступ пользователей к картам':'دسترسی کاربران به نقشه‌ها',
    'Список по умолчанию свернут. Откройте его только когда нужно изменить права.':'فهرست به‌طور پیش‌فرض بسته است. فقط هنگام تغییر دسترسی آن را باز کنید.',
    'Настроить':'تنظیم',
    'Сначала выберите участника, затем город. Галочка города открывает весь город. Если раскрыть город, можно выдать или снять доступ к каждой карте отдельно. Управляющие картами всегда имеют доступ ко всем картам.':'ابتدا عضو و سپس شهر را انتخاب کنید. علامت شهر دسترسی به کل شهر را می‌دهد. با باز کردن شهر می‌توانید دسترسی هر نقشه را جداگانه بدهید یا بردارید. مدیران نقشه همیشه به همه نقشه‌ها دسترسی دارند.',
    'Публикация':'انتشار',
    'Нажмите строку карты, чтобы увидеть максимальную награду. Публикация доступна только управляющим картами. После включения карта автоматически появляется в публичном разделе «Карты».':'برای دیدن بیشترین پاداش، ردیف نقشه را انتخاب کنید. انتشار فقط برای مدیران نقشه ممکن است. پس از فعال‌سازی، نقشه خودکار در بخش عمومی «نقشه‌ها» ظاهر می‌شود.',
    'Установка HK':'نصب HK',
    'Запуск через закладку браузера':'اجرا با نشانک مرورگر',
    'Ничего устанавливать в браузер не нужно. Закладка создаётся один раз и при каждом запуске сама загружает актуальную версию HK.':'نیازی به نصب چیزی در مرورگر نیست. نشانک را یک‌بار بسازید؛ هر بار اجرا آخرین نسخه HK خودکار بارگذاری می‌شود.',
    'Создать закладку HK':'ساخت نشانک HK',
    '★ Установить HK':'★ نصب HK',
    'Скопировать команду':'کپی دستور',
    'Показать команду вручную':'نمایش دستی دستور',
    'Адрес закладки должен начинаться с':'آدرس نشانک باید با این عبارت شروع شود',
    'Команда скопирована ✓':'دستور کپی شد ✓',
    'Дополнительный скрипт':'اسکریپت اضافی',
    'Kokkaras — слухи и реклама':'Kokkaras — شایعات و تبلیغات',
    'Автоматизация сбора слухов и рекламы. Устанавливается такой же закладкой в браузере и запускается только на странице Hamster King.':'خودکارسازی جمع‌آوری شایعات و تبلیغات. با همان نوع نشانک مرورگر نصب می‌شود و فقط در صفحه Hamster King اجرا می‌شود.',
    'Создать закладку Kokkaras':'ساخت نشانک Kokkaras',
    'Создайте в этом же браузере отдельную закладку с названием':'در همین مرورگر یک نشانک جدا با نام',
    '. Перетащите кнопку на панель закладок или скопируйте команду и вставьте её в поле':'بسازید. دکمه را به نوار نشانک‌ها بکشید یا دستور را کپی کرده و در قسمت',
    'URL / Адрес':'URL / آدرس',
    '★ Установить Kokkaras':'★ نصب Kokkaras',
    'Команда Kokkaras скопирована ✓':'دستور Kokkaras کپی شد ✓',
    'Резервный вариант':'روش جایگزین',
    'Используйте этот вариант только если запуск через закладку не работает в вашем браузере. Файл можно скачать кнопкой':'فقط اگر اجرای نشانک در مرورگر شما کار نمی‌کند از این روش استفاده کنید. فایل را با دکمه',
    '«Скачать .user.js»':'«دانلود .user.js»',
    'во вкладке «Обзор».':'در تب «نمای کلی» دانلود کنید.',
    'Обратная связь':'بازخورد',
    'Без города':'بدون شهر',
    'В этом городе нет карт.':'در این شهر نقشه‌ای وجود ندارد.',
    'Участник':'عضو',
    'управление картами':'مدیریت نقشه‌ها',
    'все города · все карты':'همه شهرها · همه نقشه‌ها',
    'Управляющий картами автоматически имеет доступ ко всем картам. Отдельные разрешения для него не требуются.':'مدیر نقشه به‌طور خودکار به همه نقشه‌ها دسترسی دارد و مجوز جداگانه لازم نیست.',
    'Весь город':'کل شهر',
    'Нет участников для настройки.':'عضوی برای تنظیم وجود ندارد.',
    'Загружаю закрытый индекс карт…':'در حال بارگذاری فهرست خصوصی نقشه‌ها…',
    'Не удалось загрузить индекс карт.':'بارگذاری فهرست نقشه‌ها ممکن نشد.',
    'Локальная карта ещё не загружена':'نقشه محلی هنوز بارگذاری نشده است',
    'нет карты':'بدون نقشه',
    'на сайте':'روی سایت',
    'На сайте':'روی سایت',
    'Закрыта':'خصوصی',
    'Карта опубликована на сайте.':'نقشه روی سایت منتشر شد.',
    'Публикация карты снята.':'انتشار نقشه برداشته شد.',
    'Сначала должна быть загружена локальная карта.':'ابتدا باید نقشه محلی بارگذاری شود.',
    'Не удалось изменить публикацию.':'تغییر وضعیت انتشار ممکن نشد.',
    'Доступ к городу выдан.':'دسترسی شهر داده شد.',
    'Доступ к городу снят.':'دسترسی شهر برداشته شد.',
    'Не удалось изменить доступ к городу.':'تغییر دسترسی شهر ممکن نشد.',
    'Доступ к карте выдан.':'دسترسی نقشه داده شد.',
    'Доступ к карте снят.':'دسترسی نقشه برداشته شد.',
    'Не удалось изменить доступ к карте.':'تغییر دسترسی نقشه ممکن نشد.',
    '✓ Скопировано':'✓ کپی شد',
    'Сессия закончилась. Войдите снова.':'نشست شما تمام شده است. دوباره وارد شوید.',
    'Не удалось загрузить кабинет. Попробуйте позже.':'بارگذاری پنل ممکن نشد. بعداً دوباره تلاش کنید.',
    'Проверяю доступ…':'در حال بررسی دسترسی…',
    'Этот Telegram ID ещё не разрешён владельцем клана.':'این شناسه تلگرام هنوز توسط مالک قبیله تأیید نشده است.',
    'Не удалось подтвердить вход через Telegram.':'تأیید ورود تلگرام ممکن نشد.',
    'Вход через Telegram пока настраивается.':'ورود با تلگرام هنوز در حال تنظیم است.',
    'Сервер входа временно недоступен.':'سرور ورود موقتاً در دسترس نیست.',
    'Введите игровой ID.':'شناسه بازی را وارد کنید.',
    'Привязываю игровой ID…':'در حال اتصال شناسه بازی…',
    'Игровой ID успешно привязан.':'شناسه بازی با موفقیت متصل شد.',
    'Этот игровой ID уже привязан к другому кабинету.':'این شناسه بازی قبلاً به حساب دیگری متصل شده است.',
    'Проверьте игровой ID и попробуйте ещё раз.':'شناسه بازی را بررسی و دوباره تلاش کنید.',
    'Готовлю файл…':'در حال آماده‌سازی فایل…',
    'Скрипт загружен.':'اسکریپت دانلود شد.',
    'Не удалось скачать скрипт.':'دانلود اسکریپت ممکن نشد.',
    'Игровой ID скопирован.':'شناسه بازی کپی شد.',
    'Не удалось скопировать ID.':'کپی شناسه ممکن نشد.',
    'Обновляю данные…':'در حال به‌روزرسانی داده‌ها…',
    'Данные обновлены.':'داده‌ها به‌روزرسانی شدند.',
    'Нет данных по общему вкладу.':'داده‌ای برای مشارکت کل وجود ندارد.',
    'По этой ветке пока нет данных.':'هنوز داده‌ای برای این شاخه وجود ندارد.',
    'Сейчас сайт восстанавливает блоки из данных игроков. Для точного зеркала скрипт должен передавать на сервер готовый снимок block → branch → participants.':'سایت اکنون بخش‌ها را از داده بازیکنان بازسازی می‌کند. برای نمایش دقیق، اسکریپت باید snapshot آماده block → branch → participants را به سرور بفرستد.',
    'Без имени':'بدون نام',
    'Chrome на iPhone не запускает такие javascript-закладки.':'Chrome در iPhone این نشانک‌های JavaScript را اجرا نمی‌کند.',
    'Откройте список закладок → Изменить → выберите':'فهرست نشانک‌ها را باز کنید → ویرایش → انتخاب کنید',
    'Удалите старый адрес и вставьте скопированную команду.':'آدرس قبلی را حذف و دستور کپی‌شده را جای‌گذاری کنید.',
    'Замените URL на скопированную команду.':'URL را با دستور کپی‌شده جایگزین کنید.',
    'Создайте обычную закладку и назовите её':'یک نشانک معمولی بسازید و نام آن را',
    'Откройте редактирование этой закладки.':'ویرایش این نشانک را باز کنید.',
    'Замените её адрес на скопированную команду и сохраните.':'آدرس آن را با دستور کپی‌شده جایگزین و ذخیره کنید.',
    'На iPhone Chrome не запускает HK из javascript-закладки. Откройте кабинет и игру в Safari.':'Chrome در iPhone نمی‌تواند HK را از نشانک JavaScript اجرا کند. پنل و بازی را در Safari باز کنید.',
    'Команда HK уже скопирована. Выполните 4 шага выше.':'دستور HK قبلاً کپی شده است. ۴ مرحله بالا را انجام دهید.',
    'Нажмите «Скопировать команду», затем выполните короткую инструкцию.':'«کپی دستور» را بزنید و سپس راهنمای کوتاه را انجام دهید.',
    'Chrome на iPhone не поддерживает запуск этой закладки. Используйте Safari.':'Chrome در iPhone اجرای این نشانک را پشتیبانی نمی‌کند. از Safari استفاده کنید.',
    'Команда HK скопирована. Выполните короткую инструкцию выше.':'دستور HK کپی شد. راهنمای کوتاه بالا را انجام دهید.',
    'Не удалось скопировать автоматически. Нажмите «Скопировать команду».':'کپی خودکار انجام نشد. «کپی دستور» را بزنید.',
    'Команда выделена — скопируйте её вручную.':'دستور انتخاب شده است — آن را دستی کپی کنید.',
    'Команда Kokkaras скопирована. Выполните короткую инструкцию выше.':'دستور Kokkaras کپی شد. راهنمای کوتاه بالا را انجام دهید.'
  };

  const exact={en:EN,fa:FA};
  const originals=new WeakMap();
  const attrs=new WeakMap();
  let language='ru';
  let observer=null;
  let scheduled=false;

  function currentLanguage(){
    const value=localStorage.getItem(KEY);
    return SUPPORTED.has(value)?value:'ru';
  }

  function preserveWhitespace(raw,translated){
    const leading=(raw.match(/^\s*/)||[''])[0];
    const trailing=(raw.match(/\s*$/)||[''])[0];
    return leading+translated+trailing;
  }

  function patternTranslate(text,lang){
    if(lang==='ru')return text;
    const d=lang==='fa'?FA:EN;
    let m;
    if((m=text.match(/^(\d+)\s+участников$/)))return lang==='fa'?m[1]+' عضو':m[1]+' members';
    if((m=text.match(/^(\d+)\s+гор\.\s*·\s*(\d+)\s+карт$/)))return lang==='fa'?m[1]+' شهر · '+m[2]+' نقشه':m[1]+' cities · '+m[2]+' maps';
    if((m=text.match(/^(\d+)\s+из\s+(\d+)\s+карт$/)))return lang==='fa'?m[1]+' از '+m[2]+' نقشه':m[1]+' of '+m[2]+' maps';
    if((m=text.match(/^(\d+)\/(\d+)\s+показано$/)))return lang==='fa'?m[1]+'/'+m[2]+' نمایش داده شد':m[1]+'/'+m[2]+' shown';
    if((m=text.match(/^Участник\s+(\d+)$/)))return lang==='fa'?'عضو '+m[1]:'Member '+m[1];
    if((m=text.match(/^Ветка\s+(\d+)$/)))return lang==='fa'?'شاخه '+m[1]:'Branch '+m[1];
    if((m=text.match(/^Клан\s+(.+)$/)))return lang==='fa'?'قبیله '+m[1]:'Clan '+m[1];
    if((m=text.match(/^Telegram ID:\s*(.+)$/)))return lang==='fa'?'شناسه تلگرام: '+m[1]:'Telegram ID: '+m[1];
    if((m=text.match(/^(\d+)\s+ур\.$/)))return lang==='fa'?m[1]+' سطح':m[1]+' lvl';
    return d[text]??text;
  }

  function translateTextNode(node){
    if(!node||!node.parentElement)return;
    const tag=node.parentElement.tagName;
    if(['SCRIPT','STYLE','TEXTAREA','CODE'].includes(tag))return;
    if(!originals.has(node))originals.set(node,node.nodeValue);
    const original=originals.get(node);
    const core=original.trim();
    if(!core)return;
    const translated=patternTranslate(core,language);
    const next=language==='ru'?original:preserveWhitespace(original,translated);
    if(node.nodeValue!==next)node.nodeValue=next;
  }

  function translateAttrs(el){
    if(!(el instanceof Element))return;
    const names=['placeholder','title','aria-label'];
    let saved=attrs.get(el);
    if(!saved){saved={};attrs.set(el,saved)}
    for(const name of names){
      if(!el.hasAttribute(name))continue;
      if(!(name in saved))saved[name]=el.getAttribute(name);
      const original=saved[name]||'';
      const translated=patternTranslate(original.trim(),language);
      el.setAttribute(name,language==='ru'?original:translated);
    }
  }

  function scan(root=document.body){
    if(!root)return;
    if(root.nodeType===Node.TEXT_NODE){translateTextNode(root);return}
    if(root.nodeType===Node.ELEMENT_NODE)translateAttrs(root);
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_ELEMENT|NodeFilter.SHOW_TEXT);
    let node;
    while((node=walker.nextNode())){
      if(node.nodeType===Node.TEXT_NODE)translateTextNode(node);
      else translateAttrs(node);
    }
  }

  function apply(lang=currentLanguage()){
    language=SUPPORTED.has(lang)?lang:'ru';
    document.documentElement.lang=language;
    document.documentElement.dir=language==='fa'?'rtl':'ltr';
    scan(document.body);
    document.title=language==='en'?'Top King Clan Member Area':
      language==='fa'?'پنل اعضای قبیله Top King':'Личный кабинет клана — Top King';
    window.dispatchEvent(new CustomEvent('tk-language-change',{detail:{language}}));
  }

  function scheduleScan(target){
    if(scheduled)return;
    scheduled=true;
    requestAnimationFrame(()=>{scheduled=false;scan(target&&target.isConnected?target:document.body)});
  }

  function init(){
    apply();
    observer=new MutationObserver(mutations=>{
      for(const mutation of mutations){
        if(mutation.type==='characterData'){scheduleScan(mutation.target);return}
        for(const node of mutation.addedNodes){
          if(node.nodeType===Node.ELEMENT_NODE||node.nodeType===Node.TEXT_NODE){scheduleScan(node);return}
        }
      }
    });
    observer.observe(document.body,{subtree:true,childList:true,characterData:true});
    window.addEventListener('storage',event=>{if(event.key===KEY)apply(currentLanguage())});
  }

  window.TopKingCabinetI18n={apply,get language(){return language}};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});
  else init();
})();