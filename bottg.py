import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- НАСТРОЙКИ ---
API_TOKEN = 'ТВОЙ_ТОКЕН'
ADMIN_ID = 8314455447  # Твой ID (узнай в @getmyid_bot)
SBP_NUMBER = "+7920157****" # Твой номер для СБП
PRICE = "99" # Цена в рублях
# -----------------

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect('maga_vpn.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, status TEXT DEFAULT 'free')''')
    conn.commit()
    conn.close()

init_db()

def generate_vless(user_id):
    # Тут будут данные твоего реального сервера после покупки
    return f"vless://uuid@ip:8443?security=reality&sni=yandex.ru#MagaVPN_{user_id}"

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    conn = sqlite3.connect('maga_vpn.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (message.from_user.id, message.from_user.username))
    conn.commit()
    conn.close()

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💎 Купить подписку (СБП)", callback_data="buy"))
    builder.row(types.InlineKeyboardButton(text="🎁 Пробный период", callback_data="trial"))
    
    await message.answer(f"Салам, {message.from_user.first_name}! 🚀\nЭто MagaVPN. Самый быстрый обход блокировок.", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "buy")
async def buy_process(callback: types.CallbackQuery):
    text = (
        f"💳 **Оплата через СБП**\n\n"
        f"1. Переведи `{PRICE}` руб. по номеру:\n`{SBP_NUMBER}`\n"
        f"2. После оплаты **пришли скриншот чека** сюда в чат.\n\n"
        "⏳ Админ проверит перевод и вышлет ключ!"
    )
    await callback.message.answer(text, parse_mode="MarkdownV2")
    await callback.answer()

# Обработка скриншота (фотографии)
@dp.message(F.photo)
async def handle_screenshot(message: types.Message):
    # Пересылаем админу
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Выдать ключ", callback_data=f"accept_{message.from_user.id}"))
    builder.row(types.InlineKeyboardButton(text="❌ Отказать", callback_data=f"decline_{message.from_user.id}"))
    
    await bot.send_photo(
        ADMIN_ID, 
        message.photo[-1].file_id, 
        caption=f"💰 Новый чек от @{message.from_user.username} (ID: {message.from_user.id})",
        reply_markup=builder.as_markup()
    )
    await message.answer("📥 Чек получен! Ожидай подтверждения от админа.")

# Обработка кнопок админа
@dp.callback_query(F.data.startswith("accept_"))
async def accept_pay(callback: types.CallbackQuery):
    user_to_pay = callback.data.split("_")[1]
    config = generate_vless(user_to_pay)
    
    await bot.send_message(user_to_pay, f"✅ Оплата подтверждена! Твой ключ:\n\n`{config}`", parse_mode="MarkdownV2")
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n🟢 ОДОБРЕНО")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
