import asyncio
import os
import asyncpg
from threading import Thread
from flask import Flask, render_template
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- НАСТРОЙКИ ---
DATABASE_URL = 'postgresql://neondb_owner:npg_wnfBSe2Pa1Ys@ep-orange-term-am7inlo4-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require' 
API_TOKEN = '8698270096:AAFr3TAqAe5nDMFjH3mS7SDiqTrzBK71tvQ'
ADMIN_ID = 8314455447
CARD_NUMBER = "2202 2061 8149 6147"
PRICE = "99"

# --- FLASK СЕРВЕР (Для Mini App и Render) ---
app = Flask(__name__, template_folder='.')

@app.route('/')
def home():
    return render_template('index.html')

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- ИНИЦИАЛИЗАЦИЯ БОТА ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- БАЗА ДАННЫХ ---
async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            expiry_time TIMESTAMP DEFAULT NULL
        )
    ''')
    await conn.close()

# --- КЛЮЧ ---
def generate_vless(user_id):
    return f"vless://e9eed10d-d0af-49c9-8a2a-4a6f48da4a4b@84.201.181.168:8443?security=reality&encryption=none&sni=yandex.com&fp=chrome&type=tcp&pbk=MHJsIaEsQByNBl7ebZIUVJNLlkxObT8_UZpxjhlb8GA&flow=xtls-rprx-vision#MukhaVPN_{user_id}"

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('INSERT INTO users (user_id, username) VALUES ($1, $2) ON CONFLICT (user_id) DO NOTHING', 
                       message.from_user.id, message.from_user.username)
    await conn.close()

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🚀 Открыть MukhaVPN", web_app=types.WebAppInfo(url="https://magavpn.onrender.com/"))) # ЗАМЕНИ НА СВОЙ URL
    builder.row(types.InlineKeyboardButton(text="💎 Купить подписку (99₽)", callback_data="buy"))
    builder.row(types.InlineKeyboardButton(text="🎁 Тест на 24 часа", callback_data="trial"))
    
    await message.answer(
        f"Салам, {message.from_user.first_name}! 👋\n\n"
        "Ты в **MukhaVPN MVP**. Это твой личный проход в свободный интернет.\n\n"
        "⚡️ Скорость: 1 Гбит/с\n"
        "🛡 Протокол: Reality\n"
        "⚙️ Сервер: Нидерланды\n\n"
        "Жми кнопку ниже, чтобы управлять подключением!", 
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "buy")
async def buy(callback: types.CallbackQuery):
    await callback.message.answer(
        f"💳 **Оплата подписки**\n\n"
        f"Цена: **{PRICE}₽ / месяц**\n"
        f"Перевод по номеру карты:\n`{CARD_NUMBER}`\n\n"
        "После оплаты пришли **скриншот чека** сюда.", 
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "trial")
async def trial(callback: types.CallbackQuery):
    key = generate_vless(callback.from_user.id)
    await callback.message.answer(f"Твой пробный ключ (на 24 часа):\n\n`{key}`", parse_mode="Markdown")
    await callback.answer()

@dp.message(F.photo)
async def handle_pay(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Одобрить", callback_data=f"ok_{message.from_user.id}"))
    builder.row(types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"no_{message.from_user.id}"))
    
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                         caption=f"💰 Чек от @{message.from_user.username}", 
                         reply_markup=builder.as_markup())
    await message.answer("✅ Чек получен! Жди подтверждения от админа.")

@dp.callback_query(F.data.startswith("ok_"))
async def ok(callback: types.CallbackQuery):
    uid = int(callback.data.split("_")[1])
    key = generate_vless(uid)
    await bot.send_message(uid, f"💎 Оплата подтверждена! Твой ключ:\n\n`{key}`", parse_mode="Markdown")
    await callback.message.edit_caption(caption="✅ Одобрено")
    await callback.answer()

@dp.callback_query(F.data.startswith("no_"))
async def no(callback: types.CallbackQuery):
    uid = int(callback.data.split("_")[1])
    await bot.send_message(uid, "❌ Чек отклонен. Свяжись с поддержкой, если это ошибка.")
    await callback.message.edit_caption(caption="🔴 Отклонено")
    await callback.answer()

# --- ЗАПУСК ---
async def main():
    await init_db()
    Thread(target=run_flask).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
