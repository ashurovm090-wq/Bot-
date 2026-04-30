import sqlite3
import asyncio
import os
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- 1. МИКРО-СЕРВЕР ДЛЯ RENDER (ЧТОБЫ БОТ НЕ УМИРАЛ) ---
app = Flask('')

@app.route('/')
def home():
    return "MagaVPN Status: Online 🚀"

def run():
    # Render использует порт 10000 по умолчанию
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. НАСТРОЙКИ БОТА ---
API_TOKEN = 'ВСТАВЬ_ТОКЕН_ТУТ'
ADMIN_ID = 8314455447  # ВСТАВЬ_СВОЙ_ID_ТУТ (цифрами)
SBP_NUMBER = "+7920157****" # Твой номер
PRICE = "99"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- 3. РАБОТА С БАЗОЙ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('maga_vpn.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, status TEXT DEFAULT 'free')''')
    conn.commit()
    conn.close()

init_db()

# Функция для генерации ссылки (пока заглушка)
def generate_vless(user_id):
    return f"vless://uuid@your_server_ip:8443?security=reality&sni=yandex.ru#MagaVPN_{user_id}"

# --- 4. ЛОГИКА БОТА ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Сохраняем юзера
    conn = sqlite3.connect('maga_vpn.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", 
                   (message.from_user.id, message.from_user.username))
    conn.commit()
    conn.close()

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💎 Купить VPN (СБП)", callback_data="buy"))
    builder.row(types.InlineKeyboardButton(text="🎁 Пробный период", callback_data="trial"))
    builder.row(types.InlineKeyboardButton(text="👨‍💻 Поддержка", url="https://t.me/твой_ник"))
    
    await message.answer(
        f"Салам, {message.from_user.first_name}! 👋\n\n"
        "Это **MagaVPN** — быстрый интернет без границ.\n"
        "Жми кнопку ниже, чтобы подключиться!",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "buy")
async def buy_process(callback: types.CallbackQuery):
    text = (
        f"💳 **ОПЛАТА ПО СБП**\n\n"
        f"1. Переведи `{PRICE}` руб. по номеру:\n`{SBP_NUMBER}`\n"
        f"2. После оплаты **пришли скриншот чека** в этот чат.\n\n"
        "⌛ Я проверю перевод и сразу вышлю тебе настройки!"
    )
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "trial")
async def trial_process(callback: types.CallbackQuery):
    await callback.message.answer("Твой пробный ключ на 24 часа:\n\n`vless://test_key_here` (Временно)")
    await callback.answer()

# --- 5. АДМИН-ПАНЕЛЬ (ОБРАБОТКА ЧЕКОВ) ---

@dp.message(F.photo)
async def handle_screenshot(message: types.Message):
    # Пересылаем чек админу с кнопками
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Одобрить", callback_data=f"accept_{message.from_user.id}"))
    builder.row(types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_{message.from_user.id}"))
    
    await bot.send_photo(
        ADMIN_ID, 
        message.photo[-1].file_id, 
        caption=f"💰 **Новый чек!**\nОт: @{message.from_user.username}\nID: `{message.from_user.id}`",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await message.answer("✅ Чек отправлен на проверку. Ожидай уведомления!")

@dp.callback_query(F.data.startswith("accept_"))
async def accept_pay(callback: types.CallbackQuery):
    user_id = callback.data.split("_")[1]
    key = generate_vless(user_id)
    
    await bot.send_message(user_id, f"🔥 **Оплата подтверждена!**\nВот твой ключ доступа:\n\n`{key}`\n\nСкопируй его и вставь в приложение v2ray/Hiddify.")
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n🟢 **ВЫДАНО**")
    await callback.answer()

@dp.callback_query(F.data.startswith("decline_"))
async def decline_pay(callback: types.CallbackQuery):
    user_id = callback.data.split("_")[1]
    await bot.send_message(user_id, "❌ Твой чек не прошел проверку. Если это ошибка, напиши в поддержку.")
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n🔴 **ОТКЛОНЕНО**")
    await callback.answer()

# --- 6. ЗАПУСК ---
async def main():
    keep_alive() # Запуск Flask для Render
    print("MagaVPN Bot запущен и ждет команд...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот выключен")
