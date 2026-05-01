import sqlite3
import asyncio
import os
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- 1. МИКРО-СЕРВЕР ДЛЯ RENDER ---
app = Flask('')
@app.route('/')
def home(): return "MagaVPN Status: Online 🚀"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) ---
API_TOKEN = '8752127884:AAEimy5lp4dhKURaioEK-TjQsGTnGzH9CQQ'
ADMIN_ID = 8314455447 # Твой ID из @getmyid_bot
SBP_NUMBER = 2202206181496147 
PRICE = "99"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- 3. ГЕНЕРАТОР РЕАЛЬНОГО КЛЮЧА ---
def generate_vless(user_id):
    # Данные из твоего JSON
    uuid = "e9eed10d-d0af-49c9-8a2a-4a6f48da4a4b"
    ip = "84.201.181.168"
    port = "8443"
    pbk = "MHJsIaEsQByNBl7ebZIUVJNLlkxObT8_UZpxjhlb8GA"
    sni = "yandex.com"
    flow = "xtls-rprx-vision"
    
    # Собираем готовую ссылку формата VLESS
    link = f"vless://{uuid}@{ip}:{port}?security=reality&encryption=none&sni={sni}&fp=chrome&type=tcp&pbk={pbk}&flow={flow}#MagaVPN_{user_id}"
    return link

# --- 4. ЛОГИКА БОТА ---
def init_db():
    conn = sqlite3.connect('maga_vpn.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT)')
    conn.commit()
    conn.close()

init_db()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    conn = sqlite3.connect('maga_vpn.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?, ?)", (message.from_user.id, message.from_user.username))
    conn.commit()
    conn.close()

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💎 Купить подписку", callback_data="buy"))
    builder.row(types.InlineKeyboardButton(text="🎁 Пробный период", callback_data="trial"))
    
    await message.answer(f"Салам, {message.from_user.first_name}! 🚀\nТвой личный MagaVPN.", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "buy")
async def buy(callback: types.CallbackQuery):
    await callback.message.answer(f"Оплата `{PRICE}` руб. на номер: `{SBP_NUMBER}`\nПришли скрин чека сюда!")
    await callback.answer()

@dp.callback_query(F.data == "trial")
async def trial(callback: types.CallbackQuery):
    key = generate_vless(callback.from_user.id)
    await callback.message.answer(f"Твой пробный ключ:\n\n`{key}`")
    await callback.answer()

@dp.message(F.photo)
async def handle_pay(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Выдать ключ", callback_data=f"ok_{message.from_user.id}"))
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"Чек от @{message.from_user.username}", reply_markup=builder.as_markup())
    await message.answer("Чек у админа! Жди подтверждения.")

@dp.callback_query(F.data.startswith("ok_"))
async def ok(callback: types.CallbackQuery):
    uid = callback.data.split("_")[1]
    key = generate_vless(uid)
    await bot.send_message(uid, f"Оплата принята! Твой ключ:\n\n`{key}`")
    await callback.message.edit_caption(caption="✅ Одобрено")
    await callback.answer()

async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
