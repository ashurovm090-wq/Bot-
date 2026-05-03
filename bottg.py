import asyncio
import os
import asyncpg
from threading import Thread
from flask import Flask, render_template
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta

# --- НАСТРОЙКИ ---
DATABASE_URL = 'postgresql://neondb_owner:npg_wnfBSe2Pa1Ys@ep-orange-term-am7inlo4-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require' 
API_TOKEN = '8698270096:AAFr3TAqAe5nDMFjH3mS7SDiqTrzBK71tvQ'
ADMIN_ID = 8314455447
CARD_NUMBER = "2202 2061 8149 6147"
PRICE = "99"

# --- FLASK СЕРВЕР ---
app = Flask(__name__, template_folder='.')

@app.route('/')
def home():
    return render_template('index.html')

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- ИНИЦИАЛИЗАЦИЯ ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

async def get_db_conn():
    return await asyncpg.connect(DATABASE_URL)

async def init_db():
    conn = await get_db_conn()
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            balance INT DEFAULT 0,
            expiry_time TIMESTAMP DEFAULT NULL
        )
    ''')
    await conn.close()

def generate_vless(user_id):
    return f"vless://e9eed10d-d0af-49c9-8a2a-4a6f48da4a4b@84.201.181.168:8443?security=reality&sni=yandex.com&fp=chrome&type=tcp&pbk=MHJsIaEsQByNBl7ebZIUVJNLlkxObT8_UZpxjhlb8GA&flow=xtls-rprx-vision#MukhaVPN_{user_id}"

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    conn = await get_db_conn()
    user = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', message.from_user.id)
    
    if not user:
        await conn.execute('INSERT INTO users (user_id, username) VALUES ($1, $2)', 
                           message.from_user.id, message.from_user.username)
        user = {'balance': 0, 'expiry_time': None}
    
    await conn.close()

    # Формируем данные для Mini App (чтобы инфа была честной)
    balance = user['balance']
    date_str = user['expiry_time'].strftime("%d.%m") if user['expiry_time'] else "не активна"
    web_url = f"https://magavpn.onrender.com/?balance={balance}&date={date_str}"

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🚀 Открыть MukhaVPN", web_app=types.WebAppInfo(url=web_url)))
    builder.row(types.InlineKeyboardButton(text="💎 Купить подписку (99₽)", callback_data="buy"))
    
    await message.answer(
        f"Салам, {message.from_user.first_name}! 👋\n\n"
        "Жми кнопку ниже, чтобы управлять подключением!", 
        reply_markup=builder.as_markup()
    )

# Ловим сигналы из Mini App (Инструкция и Оплата)
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    action = message.web_app_data.data
    
    if action == "action_setup":
        await message.answer(
            "📖 **Инструкция MukhaVPN**\n\n"
            "1. Скачай **v2rayNG** (Android) или **v2RayTun** (iOS)\n"
            "2. Скопируй свой ключ (кнопка 'Мой ключ')\n"
            "3. Импортируй в приложение через '+'\n\n"
            "Если не получается — пиши в поддержку!", 
            parse_mode="Markdown"
        )
    elif action == "action_buy":
        await buy_logic(message)

async def buy_logic(message: types.Message):
    await message.answer(
        f"💳 **Оплата подписки**\n\n"
        f"Цена: **{PRICE}₽**\n"
        f"Карта: `{CARD_NUMBER}`\n\n"
        "Пришли скриншот чека сюда.", 
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "buy")
async def buy_callback(callback: types.CallbackQuery):
    await buy_logic(callback.message)
    await callback.answer()

@dp.message(F.photo)
async def handle_pay(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Одобрить", callback_data=f"ok_{message.from_user.id}"))
    builder.row(types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"no_{message.from_user.id}"))
    
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                         caption=f"💰 Чек от @{message.from_user.username}\nID: `{message.from_user.id}`", 
                         reply_markup=builder.as_markup())
    await message.answer("✅ Чек получен! Жди подтверждения.")

@dp.callback_query(F.data.startswith("ok_"))
async def ok(callback: types.CallbackQuery):
    uid = int(callback.data.split("_")[1])
    conn = await get_db_conn()
    
    # Продлеваем подписку на 30 дней в базе
    new_expiry = datetime.now() + timedelta(days=30)
    await conn.execute('UPDATE users SET expiry_time = $1, balance = balance + 99 WHERE user_id = $2', 
                       new_expiry, uid)
    await conn.close()

    key = generate_vless(uid)
    await bot.send_message(uid, f"💎 Оплата подтверждена!\n\nТвой ключ:\n`{key}`", parse_mode="Markdown")
    await callback.message.edit_caption(caption="✅ Одобрено. Юзер получил ключ.")
    await callback.answer()

# --- ЗАПУСК ---
async def main():
    await init_db()
    Thread(target=run_flask, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
