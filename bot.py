
import logging
import json
import os
import sys
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputFile
from aiogram.utils import executor as aiogram_executor
from aiogram.utils.exceptions import MessageNotModified
from dotenv import load_dotenv
import aiofiles

load_dotenv()

# ------------------------ Конфигурация и ключи ------------------------
keys_path = os.path.join(os.path.dirname(__file__), 'keys.json')
keys: Dict = {}

if os.path.exists(keys_path):
    try:
        with open(keys_path, 'r', encoding='utf-8') as f:
            keys = json.load(f)
    except Exception:
        logging.exception('Не удалось прочитать keys.json')

BOT_TOKEN = os.getenv('BOT_TOKEN') or keys.get('BOT_TOKEN')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

LOG_PATH = os.path.join(os.path.dirname(__file__), 'bot.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler(LOG_PATH, 'a', 'utf-8'), logging.StreamHandler()]
)

# ------------------------ Работа с ролями ------------------------
def get_role(user_id: int) -> str:
    """Возвращает роль пользователя по chat_id"""
    try:
        if int(user_id) in keys.get('DEVELOPERS', []):
            return 'developer'
        if int(user_id) in keys.get('ADMINS', []):
            return 'admin'
        if int(user_id) in keys.get('USERS', []):
            return 'user'
        return 'guest'
    except Exception:
        return 'guest'

def save_keys():
    """Сохраняет keys.json на диск"""
    try:
        with open(keys_path, 'w', encoding='utf-8') as f:
            json.dump(keys, f, ensure_ascii=False, indent=2)
    except Exception:
        logging.exception('Ошибка сохранения keys.json')

# ------------------------ Основные клавиатуры ------------------------
def _main_menu_kb(role: str) -> InlineKeyboardMarkup:
    """Главное меню: заказы + (для разработчика) быстрый доступ к логам"""
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(text='📋 Заказы', callback_data='view_orders'))
    if role == 'developer':
        kb.add(InlineKeyboardButton(text='📜 Логи', callback_data='logs_open'))
    return kb

def _logs_kb(offset: int) -> InlineKeyboardMarkup:
    """Клавиатура для постраничного просмотра логов"""
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(text='📜 Показать ещё', callback_data=f'logs_more:{offset}'))
    kb.add(InlineKeyboardButton(text='🏠 Меню', callback_data='main_menu'))
    return kb

# ------------------------ Команды бота ------------------------
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    """Обработчик /start: показывает главное меню согласно роли"""
    role = get_role(message.chat.id)
    if role not in ('user', 'admin', 'developer'):
        return await message.answer('🚫 Недостаточно прав.')
    await message.answer(
        f'Здравствуйте! Ваша роль: {role}\nВыберите действие ниже:',
        reply_markup=_main_menu_kb(role)
    )

@dp.message_handler(commands=['id'])
async def cmd_id(message: types.Message):
    role = get_role(message.chat.id)
    await message.answer(f"Ваш chat_id: {message.chat.id}\nВаша роль: {role}")

@dp.message_handler(commands=['getid'])
async def get_user_id_by_username(message: types.Message):
    role = get_role(message.chat.id)
    if role not in ('admin', 'developer'):
        return await message.answer("Нет доступа.")
    args = message.get_args().strip()
    if not args:
        return await message.answer("Использование: /getid @username")
    username = args.lstrip('@')
    try:
        user = await bot.get_chat(f"@{username}")
        await message.answer(f"ID пользователя @{username}: {user.id}")
    except Exception as e:
        await message.answer(f"Не удалось найти @{username}: {e}")

# ------------------------ Управление доступом ------------------------
@dp.message_handler(commands=['grant'])
async def grant_access(message: types.Message):
    if get_role(message.chat.id) != 'developer':
        return await message.answer("Нет доступа.")
    args = message.get_args().strip().split()
    if len(args) != 2:
        return await message.answer("Использование: /grant <user_id> <role>")
    uid, role = args
    try:
        uid = int(uid)
        if role.upper() + 'S' not in keys:
            return await message.answer("Недопустимая роль. Используй admin, developer, user")
        keys[role.upper() + 'S'].append(uid)
        save_keys()
        await message.answer(f"✅ Пользователю {uid} выдана роль {role}")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.message_handler(commands=['revoke'])
async def revoke_access(message: types.Message):
    if get_role(message.chat.id) != 'developer':
        return await message.answer("Нет доступа.")
    args = message.get_args().strip().split()
    if len(args) != 1:
        return await message.answer("Использование: /revoke <user_id>")
    uid = int(args[0])
    removed = False
    for role in ['ADMINS', 'DEVELOPERS', 'USERS']:
        if uid in keys.get(role, []):
            keys[role].remove(uid)
            removed = True
    save_keys()
    await message.answer("✅ Роль удалена." if removed else "Пользователь не найден.")

# ------------------------ Перезапуск и логи ------------------------
@dp.message_handler(commands=['restart'])
async def restart_bot(message: types.Message):
    if get_role(message.chat.id) != 'developer':
        return await message.answer("🚫 Недостаточно прав.")
    await message.answer("♻️ Перезапуск бота...")
    os.execl(sys.executable, sys.executable, *sys.argv)

@dp.message_handler(commands=['logs'])
async def show_logs(message: types.Message):
    if get_role(message.chat.id) != 'developer':
        return await message.answer("🚫 Недостаточно прав.")
    await send_logs(message.chat.id, offset=0)

async def send_logs(chat_id: int, offset: int):
    """Отправляет последние 30 строк логов начиная с offset"""
    try:
        async with aiofiles.open(LOG_PATH, 'r', encoding='utf-8') as f:
            lines = await f.readlines()
        chunk = lines[-(offset + 30): -offset if offset != 0 else None]
        if not chunk:
            return await bot.send_message(chat_id, "📜 Больше логов нет.")
        text = "Последние логи:\n\n" + "".join(chunk)
        await bot.send_message(chat_id, text[-4000:], reply_markup=_logs_kb(offset + 30))
    except Exception as e:
        await bot.send_message(chat_id, f"Ошибка чтения логов: {e}")

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('logs_more:'))
async def cb_logs_more(call: CallbackQuery):
    if get_role(call.message.chat.id) != 'developer':
        return await call.answer("🚫 Недостаточно прав.", show_alert=True)
    offset = int(call.data.split(':')[1])
    await call.answer()
    await send_logs(call.message.chat.id, offset)
    # По просьбе: при нажатии "Показать ещё" отправляем файл логов
    try:
        await bot.send_document(call.message.chat.id, InputFile(LOG_PATH), caption='Файл логов')
    except Exception:
        logging.exception('Не удалось отправить файл логов')

@dp.callback_query_handler(lambda c: c.data == 'logs_open')
async def cb_logs_open(call: CallbackQuery):
    """Быстрый вход в раздел логов из меню"""
    if get_role(call.message.chat.id) != 'developer':
        return await call.answer('🚫 Недостаточно прав.', show_alert=True)
    await call.answer()
    await send_logs(call.message.chat.id, 0)

@dp.callback_query_handler(lambda c: c.data == 'main_menu')
async def cb_main_menu(call: CallbackQuery):
    """Возврат в главное меню"""
    role = get_role(call.message.chat.id)
    if role not in ('user', 'admin', 'developer'):
        return await call.answer('🚫 Недостаточно прав.', show_alert=True)
    await call.answer()
    try:
        await call.message.edit_text(
            f'Здравствуйте! Ваша роль: {role}\nВыберите действие ниже:',
            reply_markup=_main_menu_kb(role)
        )
    except MessageNotModified:
        pass

# ------------------------ Работа с заказами ------------------------
def _orders_path() -> str:
    return os.path.join(os.path.dirname(__file__), 'orders.json')

async def _load_orders() -> List[Dict]:
    path = _orders_path()
    if not os.path.exists(path):
        return []
    try:
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            content = await f.read()
            return json.loads(content)
    except Exception:
        logging.exception('Failed to load orders.json')
        return []

async def _save_orders(items: List[Dict]) -> None:
    path = _orders_path()
    async with aiofiles.open(path, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(items, ensure_ascii=False, indent=2))

def _format_order(o: Dict) -> str:
    """Форматирует один заказ для показа в боте"""
    return (
        f"🆔 ID: {o.get('id')}\n"
        f"👤 Имя: {o.get('name','-')}\n"
        f"📞 Телефон: {o.get('telephone','-')}\n"
        f"📧 Email: {o.get('email','-')}\n"
        f"📌 Тема: {o.get('subject','-')}\n"
        f"✉️ Сообщение:\n{o.get('message','-')}\n\n"
        f"⏱ Создано: {o.get('created_at','-')}\n"
        f"📦 Статус: {o.get('status','new')}"
    )

def _orders_list_kb(items: List[Dict]) -> InlineKeyboardMarkup:
    """Клавиатура со списком последних заказов и навигацией"""
    kb = InlineKeyboardMarkup()
    for o in items[-10:]:
        kb.add(InlineKeyboardButton(text=f"{o.get('name','Без имени')} | {o.get('telephone','-')}", callback_data=f"order:{o['id']}"))
    kb.add(InlineKeyboardButton(text='🏠 Меню', callback_data='main_menu'))
    return kb

def _order_details_kb(oid: str, status: str, role: str) -> InlineKeyboardMarkup:
    """Клавиатура для управления конкретным заказом"""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text='🟡 В работе', callback_data=f'order_status:{oid}:in_progress'),
        InlineKeyboardButton(text='🟢 Готово', callback_data=f'order_status:{oid}:done'),
    )
    if role in ('admin', 'developer'):
        kb.add(InlineKeyboardButton(text='🗑 Удалить', callback_data=f'order_del:{oid}'))
    kb.add(InlineKeyboardButton(text='⬅️ Назад', callback_data='view_orders'))
    return kb

# ------------------------ Управление пользователями ------------------------
@dp.message_handler(commands=['users'])
async def list_users(message: types.Message):
    role = get_role(message.chat.id)
    if role not in ('admin', 'developer'):
        return await message.answer('🚫 Недостаточно прав.')
    def fmt(role_name: str, arr):
        return f"{role_name}: " + (", ".join(map(str, arr)) if arr else '—')
    text = (
        "👥 Список пользователей по ролям:\n\n"
        f"{fmt('DEVELOPERS', keys.get('DEVELOPERS', []))}\n"
        f"{fmt('ADMINS', keys.get('ADMINS', []))}\n"
        f"{fmt('USERS', keys.get('USERS', []))}"
    )
    await message.answer(text)

async def _resolve_user_id(arg: str) -> Optional[int]:
    """Разрешает @username или число в chat_id"""
    s = arg.strip()
    if not s:
        return None
    if s.lstrip('-').isdigit():
        try:
            return int(s)
        except Exception:
            return None
    # username
    uname = s.lstrip('@')
    try:
        chat = await bot.get_chat(f"@{uname}")
        return int(chat.id)
    except Exception:
        return None

@dp.message_handler(commands=['user_add'])
async def user_add(message: types.Message):
    role = get_role(message.chat.id)
    if role not in ('admin', 'developer'):
        return await message.answer('🚫 Недостаточно прав.')
    args = message.get_args().strip().split()
    if not args:
        return await message.answer('Использование: /user_add <@username|id> [role=user|admin|developer]')
    target = args[0]
    target_role = (args[1].lower() if len(args) > 1 else 'user')
    if target_role not in ('user', 'admin', 'developer'):
        return await message.answer('Роль должна быть: user | admin | developer')
    uid = await _resolve_user_id(target)
    if not uid:
        return await message.answer('Не удалось определить пользователя по аргументу')
    key_name = target_role.upper() + 'S'
    arr = keys.setdefault(key_name, [])
    if uid not in arr:
        arr.append(uid)
        save_keys()
    await message.answer(f"✅ Пользователь {uid} добавлен в роль {target_role}")

@dp.message_handler(commands=['user_del'])
async def user_del(message: types.Message):
    role = get_role(message.chat.id)
    if role not in ('admin', 'developer'):
        return await message.answer('🚫 Недостаточно прав.')
    args = message.get_args().strip().split()
    if not args:
        return await message.answer('Использование: /user_del <@username|id> [role=user|admin|developer]')
    target = args[0]
    target_role = (args[1].lower() if len(args) > 1 else None)
    uid = await _resolve_user_id(target)
    if not uid:
        return await message.answer('Не удалось определить пользователя по аргументу')
    roles = ['USERS', 'ADMINS', 'DEVELOPERS'] if not target_role else [target_role.upper() + 'S']
    removed_any = False
    for r in roles:
        if uid in keys.get(r, []):
            keys[r].remove(uid)
            removed_any = True
    if removed_any:
        save_keys()
        return await message.answer(f'✅ Пользователь {uid} удалён из указанных ролей')
    return await message.answer('Пользователь не найден в указанных ролях')

@dp.callback_query_handler(lambda c: c.data == 'view_orders')
async def cb_view_orders(call: CallbackQuery):
    role = get_role(call.message.chat.id)
    if role not in ('user', 'admin', 'developer'):
        return await call.answer('🚫 Недостаточно прав.', show_alert=True)
    await call.answer()
    items = await _load_orders()
    text = f"Найдено заказов: {len(items)}"
    await call.message.edit_text(text, reply_markup=_orders_list_kb(items))

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('order:'))
async def cb_order_details(call: CallbackQuery):
    """Показывает детали конкретного заказа"""
    role = get_role(call.message.chat.id)
    if role not in ('user', 'admin', 'developer'):
        return await call.answer('🚫 Недостаточно прав.', show_alert=True)
    oid = call.data.split(':', 1)[1]
    await call.answer()
    items = await _load_orders()
    order = next((o for o in items if o.get('id') == oid), None)
    if not order:
        return await call.message.edit_text('Заказ не найден', reply_markup=_orders_list_kb(items))
    await call.message.edit_text(_format_order(order), reply_markup=_order_details_kb(oid, order.get('status','new'), role))

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('order_status:'))
async def cb_order_status(call: CallbackQuery):
    """Меняет статус заказа"""
    role = get_role(call.message.chat.id)
    if role not in ('user', 'admin', 'developer'):
        return await call.answer('🚫 Недостаточно прав.', show_alert=True)
    _, oid, status = call.data.split(':', 2)
    await call.answer('Статус обновлён')
    items = await _load_orders()
    updated = False
    for o in items:
        if o.get('id') == oid:
            o['status'] = status
            updated = True
            break
    if updated:
        await _save_orders(items)
    order = next((o for o in items if o.get('id') == oid), None)
    if order:
        try:
            await call.message.edit_text(_format_order(order), reply_markup=_order_details_kb(oid, order.get('status','new'), role))
        except MessageNotModified:
            pass

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('order_del:'))
async def cb_order_delete(call: CallbackQuery):
    """Удаляет заказ по ID"""
    role = get_role(call.message.chat.id)
    if role not in ('admin', 'developer'):
        return await call.answer('🚫 Недостаточно прав.', show_alert=True)
    oid = call.data.split(':', 1)[1]
    await call.answer('Удалено')
    items = await _load_orders()
    items = [o for o in items if o.get('id') != oid]
    await _save_orders(items)
    await call.message.edit_text(f'Заказ {oid} удалён. Всего заказов: {len(items)}', reply_markup=_orders_list_kb(items))

# ------------------------ API для сайта ------------------------
async def add_order_from_web(data: Dict) -> str:
    """Добавляет заказ из сайта и рассылает уведомление (без дублей получателей)"""
    items = await _load_orders()
    oid = uuid.uuid4().hex[:12]
    order = {
        'id': oid,
        'name': data.get('name') or 'Не указано',
        'telephone': data.get('telephone') or 'Не указано',
        'email': data.get('email') or 'Не указано',
        'subject': data.get('subject') or 'Без темы',
        'message': data.get('message') or 'Пустое сообщение',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'new'
    }
    items.append(order)
    await _save_orders(items)
    text = (
        f"📩 Новый заказ (ID: {oid})\n"
        f"👤 Имя: {order['name']}\n"
        f"📞 Телефон: {order['telephone']}\n"
        f"📧 Email: {order['email']}\n"
        f"📌 Тема: {order['subject']}\n"
        f"✉️ Сообщение:\n{order['message']}\n\n"
        f"⏱ Создано: {order['created_at']}\n"
        f"Статус: {order['status']}"
    )
    # Убираем дубли: если chat_id есть и в ADMINS, и в DEVELOPERS
    recipients = set()
    for role in ('ADMINS', 'DEVELOPERS'):
        for cid in keys.get(role, []):
            try:
                recipients.add(int(cid))
            except Exception:
                continue
    for cid in recipients:
        try:
            await bot.send_message(chat_id=cid, text=text)
        except Exception:
            logging.exception(f'Не удалось отправить сообщение {cid}')
    return oid

# ------------------------ Запуск ------------------------
async def start_polling() -> None:
    logging.info('Starting aiogram polling...')
    try:
        # Чистим возможный вебхук перед стартом polling
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        logging.exception('Failed to clear webhook')
    import asyncio as _asyncio
    async def _run_dp_polling():
        try:
            await dp.start_polling()
        except Exception:
            logging.exception('Dispatcher polling crashed')
    # Запускаем поллинг как задачу внутри текущего event loop FastAPI
    _asyncio.create_task(_run_dp_polling())
    logging.info('Polling started as asyncio task')
