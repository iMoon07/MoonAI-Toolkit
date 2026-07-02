import asyncio
import html
import os
import random
import threading
import signal

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from moon_core.runtime.router import moon_router
from moon_core.models import ChatRequest, Module
from moon_core.config import settings
from moon_core.logger import logger
from core.limiter import rate_limiter, ban_manager, image_limiter
from moon_core.vision import extract_ocr_text, parse_markdown_to_telegram
from moon_core.state import is_voice_active
from moon_core.supervisor import moon_supervisor
from core.identity import footer, get_help_text

# Load .env from the parent directory (Toolkit root)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

BOT_TOKEN   = os.getenv("BOT_TOKEN", "")
WEBSITE     = os.getenv("WEBSITE", "https://imoon07.github.io")
LINKEDIN    = os.getenv("LINKEDIN", "https://linkedin.com")
ALLOWED_USERS = [u.strip() for u in os.getenv("ALLOWED_USERS", "").split(",") if u.strip()]

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp  = Dispatcher()

THINKING_PHRASES = [
    "⏳ Analyzing request...",
    "⏳ Processing...",
    "⏳ Correlating context...",
    "⏳ Generating response...",
]

def is_authorized(user) -> bool:
    if not ALLOWED_USERS:
        return True
    return str(user.id) in ALLOWED_USERS or (
        user.username and user.username.lower() in [u.lower() for u in ALLOWED_USERS]
    )

def _send_to_telegram(text: str) -> str:
    """Convert LLM markdown to Telegram-safe HTML for display."""
    return parse_markdown_to_telegram(text)

async def _send_response(status_msg: Message, message: Message, raw_text: str):
    """Render and send response, splitting if over Telegram 4096 char limit."""
    ui_text = f"🌙 <b>Moon</b>\n━━━━━━━━━━━━━━━━━━━━\n{_send_to_telegram(raw_text)}\n━━━━━━━━━━━━━━━━━━━━"
    try:
        await status_msg.edit_text(ui_text)
    except Exception as e:
        err = str(e).lower()
        if "message_too_long" in err:
            chunks = [ui_text[i:i+4000] for i in range(0, len(ui_text), 4000)]
            await status_msg.edit_text(chunks[0], parse_mode=None)
            for chunk in chunks[1:]:
                await message.answer(chunk, parse_mode=None)
        elif "parse" in err or "entity" in err or "html" in err:
            await status_msg.edit_text(ui_text, parse_mode=None)
        else:
            await status_msg.edit_text(f"⚠️ <b>Error:</b> <pre>{html.escape(str(e))}</pre>")


# ========================
# /start
# ========================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    if not is_authorized(message.from_user):
        return await message.answer("⚠️ <b>Access Denied.</b>")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="[ Website ]", url=WEBSITE),
        InlineKeyboardButton(text="[ LinkedIn ]", url=LINKEDIN),
    ]])
    welcome = "🌙<b>Moon Online</b>\n\nStatus: <b>ACTIVE</b>\nEngine: Local AI via LM Studio\n\nType /help to see capabilities."
    await message.answer(welcome + footer(), reply_markup=keyboard)


# ========================
# /help
# ========================
@dp.message(Command("help"))
async def cmd_help(message: Message):
    if not is_authorized(message.from_user):
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="[ Website ]", url=WEBSITE),
        InlineKeyboardButton(text="[ LinkedIn ]", url=LINKEDIN),
    ]])
    await message.answer(get_help_text(), reply_markup=keyboard)


# ========================
# Vision (Photo)
# ========================
@dp.message(F.photo)
async def handle_photo(message: Message):
    if not is_authorized(message.from_user):
        return

    uid = message.from_user.id
    if ban_manager.is_banned(uid):
        return
    allowed, wait = image_limiter.check(uid)
    if not allowed:
        return await message.answer(f"⚠️ <b>Anti-Spam:</b> Image flood detected. Wait {wait:.1f}s.")

    if is_voice_active(message.chat.id):
        # One Reply Policy: let moon-voice handle it
        return

    # Download image
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    downloaded = await bot.download_file(file.file_path)
    tmp_dir = os.path.join(os.path.dirname(__file__), "_tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    path = os.path.join(tmp_dir, f"{file_id}.jpg")
    with open(path, "wb") as f:
        f.write(downloaded.read())

    status_msg = await message.answer("<i>📸 Extracting text via OCR...</i>")

    try:
        # OCR is the only pre-processing step — stays in bot.py by design
        ocr_text = await extract_ocr_text(path)
        caption = message.caption or "Analyze this image content."
        vision_content = f"Image Caption: {caption}\n\nOCR Result:\n```text\n{ocr_text}\n```"

        # Route through MoonAgent with vision input_type
        request = ChatRequest(
            module=Module.TELEGRAM,
            platform_user_id=str(uid),
            display_name=message.from_user.full_name or "User",
            content=vision_content,
            input_type="vision",
            intent="DEBUG",
            extra_directive="[VISION DIRECTIVE]: Analyze errors, identify root cause, propose fixes. Separate findings into: Observed Evidence / Inference / Security Indicators / Verification Steps."
        )
        response = await moon_router.chat_async(request)
        await _send_response(status_msg, message, response.text)

    except Exception as e:
        logger.error(f"Vision handler error: {e}")
        await status_msg.edit_text(f"⚠️ <b>Vision Error:</b> <pre>{html.escape(str(e))}</pre>")


# ========================
# Text
# ========================
@dp.message(F.text)
async def handle_text(message: Message):
    if not is_authorized(message.from_user):
        return
    if message.text.startswith("!"):
        return  # Reserved for voice agent commands

    uid = message.from_user.id
    if ban_manager.is_banned(uid):
        return
    allowed, wait = rate_limiter.check(uid)
    if not allowed:
        return await message.answer(f"⚠️ <b>Rate Limit:</b> Too fast. Wait {wait:.1f}s.")

    if is_voice_active(message.chat.id):
        # One Reply Policy: let moon-voice handle it
        return

    status_msg = await message.answer(f"<i>{random.choice(THINKING_PHRASES)}</i>")

    try:
        request = ChatRequest(
            module=Module.TELEGRAM,
            platform_user_id=str(uid),
            display_name=message.from_user.full_name or "User",
            content=message.text,
            input_type="text",
            intent="CHAT"
        )
        llm_task = asyncio.create_task(moon_router.chat_async(request))
        moon_supervisor.register(llm_task)
        response = await llm_task
        await _send_response(status_msg, message, response.text)

    except Exception as e:
        logger.error(f"Text handler error: {e}")
        await status_msg.edit_text(f"⚠️ <b>Error:</b> <pre>{html.escape(str(e))}</pre>")


# ========================
# Console Listener
# ========================
def _console_listener():
    while True:
        try:
            cmd = input()
            if cmd.strip().lower() in ["quit", "exit", "stop"]:
                print("🌙 Shutting down Moon Bot via console...")
                os.kill(os.getpid(), signal.SIGINT)
                break
        except (EOFError, KeyboardInterrupt):
            pass


async def main():
    logger.boot("🌙 Moon Bot V3 — MoonAgent Pipeline initialized")
    logger.info(f"Model loaded: {settings.model_name}")
    logger.info("Session started")
    print("Type 'quit' to stop gracefully.\n")
    
    moon_supervisor.install_signal()
    
    async def _close_bot():
        print("   [Hook] Closing Aiogram session...")
        await bot.session.close()
    
    moon_supervisor.add_shutdown_hook(_close_bot)
    
    threading.Thread(target=_console_listener, daemon=True).start()
    
    try:
        await dp.start_polling(bot)
    finally:
        pass


if __name__ == "__main__":
    asyncio.run(main())
