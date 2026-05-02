import asyncio
import os
import asyncpg
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- КОНФИГУРАЦИЯ ---
# Ссылка на Neon (PostgreSQL)
DATABASE_URL = 'postgresql://neondb_owner:npg_wnfBSe2Pa1Ys@ep-orange-term-am7inlo4-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require' 
# Твой новый токен от BotFather
API_TOKEN = '8698270096:AAFr3TAqAe5nDMFjH3mS7SDiqTrzBK71tvQ'
# Твой ID и настройки оплаты
ADMIN_ID = 8314455447
CARD_NUMBER = "2202 2061 8149 6147"
PRICE = "99"

# --- СЕРВЕР ДЛЯ ПОДДЕРЖКИ АКТИВНОСТИ ---
app = Flask('')
@app.route('/')
def home(): return "MagaVPN Status: Online 🚀"

def run():
    # На Render порт 10000, на Koyeb 8080. Этот код подстроится сам.
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- РАБОТА С БАЗОЙ ДАННЫХ (POSTGRESQL) ---
async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT
        )
    ''')
    await conn.close()

# --- ГЕНЕРАТОР КЛЮЧА ---
def generate_vless(user_id):
    uuid = "e9eed10d-d0af-49c9-8a2a-4a6f48da4a4b"
    ip = "84.201.181.168"
    port = "8443"
    pbk = "MHJsIaEsQByNBl7ebZIUVJNLlkxObT8_UZpxjhlb8GA"
    sni = "yandex.com"
    flow = "xtls-rprx-vision"
    return f"vless://{uuid}@{ip}:{port}?security=reality&encryption=none&sni={sni}&fp=chrome&type=tcp&pbk={pbk}&flow={flow}#MagaVPN_{user_id}"

# --- ЛОГИКА БОТА ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Сохраняем юзера в облачную БД Neon
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute('INSERT INTO users (user_id, username) VALUES ($1, $2) ON CONFLICT (user_id) DO NOTHING', 
                           message.from_user.id, message.from_user.username)
        await conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💎 Купить подписку (99₽)", callback_data="buy"))
    builder.row(types.InlineKeyboardButton(text="🎁 Пробный период", callback_data="trial"))
    builder.row(types.InlineKeyboardButton(text="📖 Как подключить?", callback_data="help"))
    
    welcome_text = (
        f"Салам, {message.from_user.first_name}! 🚀\n\n"
        "Добро пожаловать в **MagaVPN**.\n"
        "Личный сервер на протоколе Reality (не блокируется).\n\n"
        "⚡️ Скорость: до 1 Гбит/с\n"
        "🌍 Локация: Нидерланды"
    )
    await message.answer(welcome_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "buy")
async def buy(callback: types.CallbackQuery):
    pay_text = (
        "💳 **ОПЛАТА ПО КАРТЕ / СБП**\n\n"
        f"Сумма: **{PRICE}₽**\n"
        f"Номер карты: `{CARD_NUMBER}`\n\n"
        "После перевода **пришли скриншот чека** в этот чат. "
        "Админ проверит его и выдаст тебе доступ!"
    )
    await callback.message.answer(pay_text, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "trial")
async def trial(callback: types.CallbackQuery):
    key = generate_vless(callback.from_user.id)
    await callback.message.answer(f"Твой пробный ключ (нажми для копирования):\n\n`{key}`", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "help")
async def help_info(callback: types.CallbackQuery):
    help_text = (
        "📖 **ИНСТРУКЦИЯ ПО ПОДКЛЮЧЕНИЮ**\n\n"
        "1️⃣ **Скачай приложение:**\n"
        "— iOS: [V2Box](https://apps.apple.com/app/v2box-v2ray-client/id1640135277)\n"
        "— Android: [v2rayNG](https://play.google.com/store/apps/details?id=com.v2ray.ang)\n\n"
        "2️⃣ Скопируй ключ, нажми **(+)** или **Import from Clipboard**."
    )
    await callback.message.answer(help_text, parse_mode="Markdown", disable_web_page_preview=True)
    await callback.answer()

# --- АДМИНКА ---
@dp.message(F.photo)
async def handle_pay(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Одобрить", callback_data=f"ok_{message.from_user.id}"))
    builder.row(types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"no_{message.from_user.id}"))
    
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                         caption=f"💰 Новый чек от @{message.from_user.username}", 
                         reply_markup=builder.as_markup())
    await message.answer("📥 Чек отправлен админу. Ожидай подтверждения!")

@dp.callback_query(F.data.startswith("ok_"))
async def ok(callback: types.CallbackQuery):
    uid = int(callback.data.split("_")[1])
    key = generate_vless(uid)
    await bot.send_message(uid, f"✅ Оплата принята!\nТвой личный ключ:\n\n`{key}`", parse_mode="Markdown")
    await callback.message.edit_caption(caption="✅ Одобрено")
    await callback.answer()

@dp.callback_query(F.data.startswith("no_"))
async def no(callback: types.CallbackQuery):
    uid = int(callback.data.split("_")[1])
    await bot.send_message(uid, "❌ Твой чек был отклонен. Проверь данные или напиши в поддержку.")
    await callback.message.edit_caption(caption="🔴 Отклонено")
    await callback.answer()

# --- ЗАПУСК ---
async def main():
    await init_db()
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
