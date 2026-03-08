# ТехДом: сайт + Telegram-бот + SQLite

Проект объединяет:
- web-приложение на `Litestar`;
- Telegram-бота на `aiogram`;
- SQLite-базу данных через `SQLAlchemy` и миграции `Alembic`.

Один запускной файл `main.py` умеет поднимать сайт, бота или оба процесса сразу.

## Что внутри

- `app/web/` — web-маршруты, шаблоны и логика сайта.
- `app/bot/` — роутеры Telegram-бота, клавиатуры и команды администрирования.
- `app/services/` — бизнес-логика для заявок, ролей и уведомлений.
- `app/db/` — модели, сессии и репозитории.
- `alembic/` — миграции базы данных.
- `templates/` — HTML-шаблоны сайта.
- `static/` — CSS, JS и изображения.
- `tests/` — автотесты.
- `scripts/migrate_json_to_sqlite.py` — перенос legacy-данных из JSON в SQLite.

## Требования

- Windows PowerShell или совместимый shell.
- Python `3.11+`.
- Доступ к интернету для Telegram-бота.
- Токен Telegram-бота, если планируется запуск bot-части.

## Установка

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Настройка `.env`

1. Скопируйте `.env.example` в `.env`.
2. Заполните переменные окружения.

| Переменная | Обязательна | Значение по умолчанию | Назначение |
| --- | --- | --- | --- |
| `BOT_TOKEN` | Да для бота | пусто | Токен Telegram-бота |
| `BOT_MODE` | Нет | `polling` | Режим запуска бота: `polling` или `webhook` |
| `DATABASE_URL` | Нет | `sqlite+aiosqlite:///.../app.db` | URL базы данных |
| `BOT_WEBHOOK_URL` | Нет | пусто | Базовый HTTPS URL для webhook |
| `BOT_WEBHOOK_PATH` | Нет | `/webhook` | Путь webhook |
| `BOT_WEBHOOK_HOST` | Нет | `0.0.0.0` | Хост для локального webhook-сервера |
| `BOT_WEBHOOK_PORT` | Нет | `8081` | Порт для локального webhook-сервера |

Для локальной разработки достаточно:
- указать `BOT_TOKEN`;
- оставить `BOT_MODE=polling`;
- не задавать `DATABASE_URL`, если подходит SQLite в корне проекта.

## Миграции базы данных

Применить все миграции:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Если база еще не создана, миграции создадут нужные таблицы.

## Импорт legacy JSON

Если остались старые файлы `orders.json` и `keys.json`, перенесите их в SQLite:

```powershell
.\.venv\Scripts\python.exe scripts\migrate_json_to_sqlite.py
```

Особенности:
- уже существующие записи не дублируются;
- резервные копии `*.bak` создаются только если действительно были импортированы новые данные;
- роли из `keys.json` поднимаются с учетом приоритета `developer > admin > user`.

## Запуск

### Запуск web + bot одним процессом

```powershell
.\.venv\Scripts\python.exe main.py
```

### Только web

```powershell
.\.venv\Scripts\python.exe main.py --mode web --host 0.0.0.0 --port 5000
```

### Только bot

```powershell
.\.venv\Scripts\python.exe main.py --mode bot
```

### Альтернативные entrypoint-файлы

```powershell
.\.venv\Scripts\python.exe main_web.py
.\.venv\Scripts\python.exe main_bot.py
```

## Webhook-режим

Понадобится только если бот работает за HTTPS и reverse proxy.

Минимальная схема:
1. Установите `BOT_MODE=webhook`.
2. Заполните `BOT_WEBHOOK_URL`.
3. При необходимости задайте `BOT_WEBHOOK_PATH`, `BOT_WEBHOOK_HOST`, `BOT_WEBHOOK_PORT`.
4. Перезапустите бот.

Если `BOT_MODE=webhook`, но `BOT_WEBHOOK_URL` пустой, бот автоматически переключится в `polling`.

## Автотесты

Полный прогон:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Полезные выборочные прогоны:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_web_routes.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_bot_logs.py
```

## Основные маршруты сайта

- `/`
- `/Price`
- `/price`
- `/price1`
- `/price2`
- `/price3`
- `/obrsvaz`
- `/services/{slug}`
- `/feedback`
- `/assets/{filename:path}`
- `/static/{filename:path}` — legacy-redirect на `/assets/...`

## Структура данных

### База данных

По умолчанию используется SQLite-файл:

```text
app.db
```

Основные таблицы:
- `orders` — заявки из сайта и бота;
- `users` — пользователи Telegram и их роли.

### Роли пользователей

Поддерживаются роли:
- `user`
- `admin`
- `developer`

Если пользователь не найден в БД, сервисы считают его `guest`.

## Эксплуатация и обслуживание

### Где находится лог

Лог-файл по умолчанию:

```text
bot.log
```

Он создается автоматически при запуске web и bot компонентов.

### Где смотреть данные БД

Быстрая проверка таблиц и последних заявок через Python:

```powershell
@'
import sqlite3

conn = sqlite3.connect("app.db")
cur = conn.cursor()

print("Таблицы:")
for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print("-", row[0])

print("\nПоследние 10 заявок:")
for row in cur.execute("""
SELECT id, name, telephone, status, source, created_at
FROM orders
ORDER BY created_at DESC
LIMIT 10
"""):
    print(row)

print("\nПользователи и роли:")
for row in cur.execute("SELECT telegram_id, role FROM users ORDER BY telegram_id"):
    print(row)

conn.close()
'@ | .\.venv\Scripts\python.exe -
```

### Как выдать роль пользователю

Через Telegram-команды:
- `/grant <user_id> <role>` — только для `developer`;
- `/revoke <user_id>` — только для `developer`;
- `/role_set <@username|id> <role>` — назначить роль по `username` или `user_id`;
- `/role_del <@username|id>` — удалить роль по `username` или `user_id`;
- `/user_add <@username|id> <role>` — алиас для `/role_set`;
- `/user_del <@username|id>` — алиас для `/role_del`;
- `/users` — список пользователей по ролям.

Ограничения:
- `admin` может управлять ролями `user` и `admin`;
- роль `developer` назначает и удаляет только `developer`.

### Как настроить, кто получает новые заявки

Получатели уведомлений о новых заявках определяются ролями `admin` и `developer`.

Команды:
- `/notify_add <@username|id> [role=admin|developer]` — добавить получателя заявок;
- `/notify_del <@username|id>` — убрать из получателей заявок;
- `/notify_list` — показать текущих получателей новых заявок.

### Как посмотреть логи из бота

Команда:

```text
/logs
```

Поведение:
- показываются последние 30 строк;
- кнопка "Показать ещё" листает логи назад;
- лог читается с конца файла, без загрузки всего файла в память.

## Рекомендованный порядок запуска перед релизом

1. Обновить зависимости и активировать `.venv`.
2. Проверить `.env`.
3. Выполнить `alembic upgrade head`.
4. Прогнать `pytest -q`.
5. Проверить главную страницу и страницы услуг.
6. Отправить тестовую форму `/feedback`.
7. Проверить, что бот отвечает на `/start`.
8. Проверить `/logs` и выдачу ролей.

## Типовые проблемы

### `BOT_TOKEN is required`

Причина:
- в `.env` не заполнен `BOT_TOKEN`.

Решение:
- добавьте токен и перезапустите процесс.

### `No module named app`

Причина:
- команда запущена не из корня проекта.

Решение:
- запускайте `python main.py`, `pytest` и миграции из корневой папки репозитория.

### Пустая БД или отсутствуют таблицы

Причина:
- не были применены миграции.

Решение:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

### Бот не отправляет уведомления

Проверьте:
- заполнен ли `BOT_TOKEN`;
- есть ли в таблице `users` получатели с ролями `admin` или `developer`;
- виден ли Telegram-боту нужный пользователь.

### В webhook-режиме бот не поднимается как ожидалось

Проверьте:
- `BOT_MODE=webhook`;
- заполнен ли `BOT_WEBHOOK_URL`;
- доступен ли внешний HTTPS URL.

Если `BOT_WEBHOOK_URL` пустой, код автоматически уйдет в `polling`.

## Краткий чек-лист перед релизом

- `.env` заполнен и не попадает в git.
- `.venv` создан и зависимости установлены.
- Миграции применены.
- Тесты проходят.
- На страницах услуг нет битых изображений.
- `/assets/main.css` открывается напрямую.
- Форма обратной связи создает заявку.
- Бот отвечает на `/start`.
- Админские команды работают.
- `bot.log` создается и читается.
