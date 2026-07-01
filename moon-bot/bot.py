import asyncio
import os
import html
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, WEBSITE, LINKEDIN, ALLOWED_USERS
from core.router import detect_intent
from core.limiter import rate_limit, is_banned, image_limit
from core.llm import generate_response
from core.vision import analyze_image
from core.identity import footer, get_help_text

# Initialize Bot with HTML ParseMode globally for neat outputs
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

def is_authorized(user):
    if not ALLOWED_USERS:
        return True
    return str(user.id) in ALLOWED_USERS or (user.username and user.username.lower() in [u.lower() for u in ALLOWED_USERS])


@dp.message(Command("start"))
async def cmd_start(message: Message):
    if not is_authorized(message.from_user):
        return await message.answer("⚠️ <b>Access Denied:</b> Lu siapa bro? Bot ini punya iMoon.")

    welcome_text = (
        "🌙<b>Moon CLI Online</b>\n\n"
        "Status: <b>ACTIVE</b>\n"
        "Engine: Local / Cloud Hybrid AI\n\n"
        "Type /help to see capabilities."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="[ Website ]", url=WEBSITE),
            InlineKeyboardButton(text="[ LinkedIn ]", url=LINKEDIN)
        ]
    ])
    await message.answer(welcome_text + footer(), reply_markup=keyboard)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    if not is_authorized(message.from_user):
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="[ Website ]", url=WEBSITE),
            InlineKeyboardButton(text="[ LinkedIn ]", url=LINKEDIN)
        ]
    ])
    await message.answer(get_help_text(), reply_markup=keyboard)

@dp.message(F.photo)
async def handle_photo(message: Message):
    if not is_authorized(message.from_user):
        return
        
    user_id = message.from_user.id

    if is_banned(user_id):
        return

    if not image_limit(user_id):
        return await message.answer("⚠️ <b>Anti-Spam Active:</b> Image flood detected.")

    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    downloaded = await bot.download_file(file.file_path)

    # Make sure /tmp directory exists or use a local one
    os.makedirs("/tmp", exist_ok=True)
    path = f"/tmp/{file_id}.jpg"
    with open(path, "wb") as f:
        f.write(downloaded.read())

    status_msg = await message.answer("<i>📸 Extracting text via OCR...</i>")
    result = await analyze_image(path, message.caption)
    return await status_msg.edit_text(result)

@dp.message(F.text)
async def handle_text(message: Message):
    if not is_authorized(message.from_user):
        return
        
    # Ignore commands prefixed with '!' (handled by voice agent)
    if message.text.startswith("!"):
        return
        
    user_id = message.from_user.id

    if is_banned(user_id):
        return

    if not rate_limit(user_id):
        return await message.answer("⚠️ <b>Rate Limit:</b> Too fast. Please slow down.")

    # Send a temporary processing message
    import random
    phrases = [
        "⏳ Analyzing request...",
        "⏳ Processing...",
        "⏳ Correlating context...",
        "⏳ Generating response..."
    ]
    status_msg = await message.answer(f"<i>{random.choice(phrases)}</i>")

    intent = detect_intent(message.text)
    response = await generate_response(message.text, intent, user_id)

    # Format terminal-style UI
    ui_response = f"🌙 <b>Moon CLI System</b>\n━━━━━━━━━━━━━━━━━━━━\n{response}\n━━━━━━━━━━━━━━━━━━━━"

    # Edit the temporary message with the actual AI response
    try:
        await status_msg.edit_text(ui_response)
    except Exception as e:
        error_msg = str(e).lower()
        if "message_too_long" in error_msg:
            # Split message if it exceeds Telegram's 4000 char limit
            chunks = [ui_response[i:i+4000] for i in range(0, len(ui_response), 4000)]
            await status_msg.edit_text(chunks[0], parse_mode=None)
            for chunk in chunks[1:]:
                await message.answer(chunk, parse_mode=None)
        elif "parse" in error_msg or "entity" in error_msg or "html" in error_msg:
            # Fallback to raw text if HTML parsing fails
            await status_msg.edit_text(ui_response, parse_mode=None)
        else:
            await status_msg.edit_text(f"⚠️ <b>Error:</b> <pre>{str(e)}</pre>")
import threading

def console_listener():
    while True:
        try:
            cmd = input()
            if cmd.strip().lower() in ['quit', 'exit', 'stop']:
                print("🌙 Shutting down Moon Bot...")
                os._exit(0)
        except (EOFError, KeyboardInterrupt):
            os._exit(0)

async def main():
    print("="*50)
    print("🌙 Moon Bot V2 (Text Engine)")
    print("STATUS : ACTIVE")
    print("DEV    : iMoon")
    print("="*50)
    print("Type 'quit' to stop gracefully.\n")
    # Start a background thread to listen for console input
    threading.Thread(target=console_listener, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
