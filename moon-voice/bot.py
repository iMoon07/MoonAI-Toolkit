"""
moon-voice/bot.py
=================
Thin UI wrapper for the MoonAI Voice Userbot.
All LLM, Memory, and Prompt logic is handled by moon_core.MoonAgent.

Voice flow:
  User sends Voice Note
    -> pyrogram downloads OGG
    -> pydub converts OGG to WAV
    -> faster-whisper transcribes WAV (offline, local)
    -> ChatRequest(input_type="voice") sent to MoonAgent
    -> MoonAgent queries LLM, saves to moon_memory.db
    -> clean_for_tts() strips markdown
    -> edge-tts generates MP3
    -> pyrogram uploads MP3 back as Voice Note
    -> cleanup all temp files
"""

import asyncio
import html
import os
import re
import uuid
import time
import signal
import sys
import threading

from dotenv import load_dotenv
from pydub import AudioSegment
from pyrogram import Client, filters
from pyrogram.errors import MessageNotModified
from pytgcalls import PyTgCalls, idle
from pytgcalls.types import MediaStream, AudioQuality
import edge_tts

from moon_core.runtime.router import moon_router
from moon_core.config import settings
from moon_core.logger import logger
from moon_core.models import ChatRequest, Module
from moon_core.vision import extract_ocr_text
from moon_core.state import set_voice_active, set_voice_inactive, is_voice_active
from moon_core.policy import policy_engine
from moon_core.supervisor import moon_supervisor
from controller import voice_controller
from telegramify_markdown import convert as md_convert
from telegramify_markdown import split_entities, utf16_len
from telegramify_markdown.type import MessageEntity as TgEntity

import pyrogram.utils
pyrogram.utils.MIN_CHANNEL_ID = -10099999999999

load_dotenv()

API_ID    = os.getenv("API_ID", "")
API_HASH  = os.getenv("API_HASH", "")
ALLOWED_USERS_RAW = os.getenv("ALLOWED_USERS", "")
def _parse_user(u):
    u = u.strip()
    try:
        return int(u)
    except ValueError:
        return u
ALLOWED_USERS = [_parse_user(u) for u in ALLOWED_USERS_RAW.split(",")] if ALLOWED_USERS_RAW else []
TTS_VOICE = os.getenv("TTS_VOICE", "id-ID-ArdiNeural")

WHISPER_MODEL  = os.getenv("WHISPER_MODEL", "small")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")

# =========================
# WHISPER INITIALIZATION
# =========================
try:
    from faster_whisper import WhisperModel
    logger.info(f"Loading Whisper Model ({WHISPER_MODEL}) on {WHISPER_DEVICE}...")
    whisper_model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type="int8")
    logger.info("Whisper model loaded.")
    WHISPER_AVAILABLE = True
except ImportError:
    logger.warning("faster-whisper not installed. Voice transcription will fail.")
    whisper_model = None
    WHISPER_AVAILABLE = False

# =========================
# PYROGRAM + PYTGCALLS
# =========================
app      = Client("moon_voice_session", api_id=API_ID, api_hash=API_HASH)
call_py  = PyTgCalls(app)

# Per-chat async lock to prevent concurrent LLM calls for the same chat
_chat_locks: dict = {}

def _get_lock(chat_id: int) -> asyncio.Lock:
    if chat_id not in _chat_locks:
        _chat_locks[chat_id] = asyncio.Lock()
    return _chat_locks[chat_id]

# =========================
# STT (Speech-to-Text)
# =========================
def _transcribe(wav_path: str) -> str:
    """Blocking Whisper transcription — must be called via asyncio.to_thread."""
    if not WHISPER_AVAILABLE or whisper_model is None:
        raise RuntimeError("Whisper not initialized. STT is offline.")
    segments, _ = whisper_model.transcribe(wav_path, beam_size=5, language="id")
    return " ".join(seg.text for seg in segments).strip()

# =========================
# TTS (Text-to-Speech)
# =========================
def clean_for_tts(text: str) -> str:
    """Strip markdown, code blocks, and paths — produce clean speakable text."""
    text = re.sub(r'```.*?```', ' [cek kodenya di chat] ', text, flags=re.DOTALL)
    text = re.sub(r'`.*?`', '', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'[(){}<>\[\]]', '', text)
    text = re.sub(r'(/[a-zA-Z0-9_\-\.]+)+', '', text)
    text = re.sub(r'([a-zA-Z]:\\[^\s]+)', '', text)
    text = re.sub(r'[*_#\-]', '', text)
    text = re.sub(r'\n+', '. ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('. .', '.')
    text = text.strip()
    
    # Auto-Chunking (Voice Controller) - Smart Sentence Split
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    final_sentences = []
    for s in sentences:
        if len(s) > 300:
            final_sentences.extend([p.strip() for p in s.split(',') if p.strip()])
        else:
            final_sentences.append(s)
            
    if len(final_sentences) > 3:
        return '. '.join(final_sentences[:3]) + '. (Teks dipotong, mau dibahas lebih lanjut?)'
    return '. '.join(final_sentences) + ('.' if final_sentences and not text.endswith('.') else '')

async def _generate_tts(text: str) -> str:
    """Generate MP3 via edge-tts, return path."""
    if not text or not text.strip():
        text = "Maaf Kapten, Moon tidak mendapatkan jawaban dari server."
    filename = f"tts_{uuid.uuid4().hex}.mp3"
    communicate = edge_tts.Communicate(text, TTS_VOICE)
    await communicate.save(filename)
    return filename

async def _play_and_cleanup(chat_id: int, filename: str):
    """Play audio in VC and delete the file after playback."""
    try:
        if not os.path.exists(filename) or os.path.getsize(filename) < 500:
            raise RuntimeError(f"Playback aborted: {filename} is invalid or too small.")

        audio = await asyncio.to_thread(AudioSegment.from_file, filename, format="mp3")
        duration = len(audio) / 1000.0
        await call_py.play(chat_id, MediaStream(filename, audio_parameters=AudioQuality.HIGH))
        await asyncio.sleep(duration + 1.0)
    finally:
        if os.path.exists(filename):
            os.remove(filename)
            logger.debug(f"Cleaned up TTS file: {filename}")


@app.on_message(filters.text | filters.photo, group=-1)
async def incoming_logger(client, message):
    if message.outgoing:
        return
    text = message.text or message.caption or ""
    if text.startswith("!") or is_voice_active(message.chat.id):
        user_name = message.from_user.first_name if message.from_user else "Unknown"
        logger.info(f"📡 [INCOMING] {text[:50]}... | Chat: {message.chat.id} | User: {user_name}")

# =========================
# VOICE COMMANDS
# =========================
@app.on_message(filters.command("join", prefixes="!") & (filters.me | filters.user(ALLOWED_USERS)))
async def join_vc(client, message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    name = message.from_user.first_name or "Kapten"
    await message.reply_text("🔄 Joining Voice Chat...")
    
    # Clear context for the session
    request = ChatRequest(
        module=Module.VOICE,
        platform_user_id=user_id,
        display_name=name,
        content="",
        intent="CHAT"
    )
    moon_router.clear_context(request)
    
    try:
        greeting_text = "Halo Kapten, Moon Voice siap. Hari ini mau belajar apa? Moon bakal analisa, kasih challenge, dan jadi partner diskusi."
        filename = await _generate_tts(greeting_text)
        await _play_and_cleanup(chat_id, filename)
        set_voice_active(chat_id)
        
        await message.reply_text(
            "✅ Connected!\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🌙 Moon is listening...\n"
            "Mode : Voice Partner\n"
            "Status : Active\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Silakan bicara atau kirim gambar untuk dianalisa."
        )
    except Exception as e:
        logger.error(f"!join error: {e}")
        await message.reply_text(f"❌ Gagal: {html.escape(str(e))}")


@app.on_message(filters.command("leave", prefixes="!"))
async def leave_vc(client, message):
    chat_id = message.chat.id
    set_voice_inactive(chat_id)
    try:
        await call_py.leave_group_call(chat_id)
    except Exception:
        pass
    await message.reply_text("👋 Moon telah meninggalkan Voice Chat. Mode Voice Partner dinonaktifkan.")

def chunk_text_smart(text, max_len=3500):
    chunks = []
    current_chunk = ""
    for paragraph in text.split("\n\n"):
        if len(current_chunk) + len(paragraph) + 2 > max_len:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
            else:
                chunks.append(paragraph[:max_len])
                current_chunk = paragraph[max_len:] + "\n\n"
        else:
            current_chunk += paragraph + "\n\n"
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks


async def _reply_md(target, chat_text: str, header: str = "") -> None:
    """
    Convert markdown chat_text using telegramify-markdown and send via Pyrogram.
    Pyrogram supports 'entities' kwarg directly on send_message/edit.
    Splits automatically if text is too long.
    """
    body_text, body_entities = md_convert(chat_text)

    if header:
        offset_shift = utf16_len(header)
        shifted = [
            TgEntity(
                type=e.type, offset=e.offset + offset_shift,
                length=e.length, url=e.url,
                language=e.language, custom_emoji_id=e.custom_emoji_id
            )
            for e in body_entities
        ]
        full_text = header + body_text
        all_entities = shifted
    else:
        full_text = body_text
        all_entities = body_entities

    chunks = list(split_entities(full_text, all_entities, max_utf16_len=4090))

    first_text, first_ents = chunks[0]
    await target.edit(
        first_text,
        entities=[e.to_dict() for e in first_ents]
    )
    for chunk_text, chunk_ents in chunks[1:]:
        await target.reply(
            chunk_text,
            entities=[e.to_dict() for e in chunk_ents]
        )


async def process_request(client, message, chat_id, user_text, photo_to_analyze=None):
    user_id = str(message.from_user.id)
    name = message.from_user.first_name or "Kapten"
    
    voice_controller.stop_flag = False
    
    # If in voice mode, stop the current TTS playback immediately! (Interruption)
    if is_voice_active(chat_id):
        try:
            await call_py.pause_stream(chat_id)
        except Exception:
            pass

    lock = _get_lock(chat_id)
    warning_msg = None
    if lock.locked():
        warning_msg = await message.reply_text("⏳ Moon masih sibuk mikir, antre bentar ya kapten...")

    async with lock:
        if warning_msg:
            try:
                await warning_msg.delete()
            except Exception:
                pass
                
        overall_start = time.time()
        status = await message.reply_text(f"🧠 Moon lagi mikir...")
        
        try:
            is_voice = is_voice_active(chat_id)
            if is_voice:
                extra_directive = (
                    "[VOICE DIRECTIVE]: Bertindaklah sebagai AI Study Companion. Berikan analisa mendalam. "
                    "WAJIB pisahkan outputmu menjadi dua bagian persis seperti ini:\n"
                    "[VOICE]\n(Maksimal 80 kata! Ringkasan pendek untuk diucapkan. Sapaan akrab, intonasi ngobrol santai. Jangan membaca poin seperti 'Poin pertama' atau 'Kesimpulannya'. Bicara natural seperti podcast.)\n[/VOICE]\n"
                    "[CHAT]\n(Analisis lengkap mendalam dengan markdown untuk dibaca di chat.)\n[/CHAT]"
                )
            else:
                extra_directive = "[VOICE DIRECTIVE]: Ringkas, conversational, hindari markdown dan code blocks. Kalau ada command, bilang saja 'gue kirim kodenya di chat ya'."

            if photo_to_analyze:
                await status.edit_text("📸 Membaca gambar...")
                photo_path = await client.download_media(photo_to_analyze)
                
                t_ocr = time.time()
                ocr_text = await extract_ocr_text(photo_path)
                ocr_time = time.time() - t_ocr
                
                await status.edit_text("📝 OCR selesai...")
                if not ocr_text or not ocr_text.strip():
                    ocr_text = "OCR gagal membaca teks atau gambar kosong."
                
                request = ChatRequest(
                    module=Module.VOICE,
                    platform_user_id=user_id,
                    display_name=name,
                    content=f"Image Caption: {user_text}\n\nOCR Result:\n```text\n{ocr_text}\n```",
                    input_type="vision",
                    intent="CHAT",
                    extra_directive=extra_directive
                )
            else:
                request = ChatRequest(
                    module=Module.VOICE,
                    platform_user_id=user_id,
                    display_name=name,
                    content=user_text,
                    input_type="text",
                    intent="CHAT",
                    extra_directive=extra_directive
                )
            
            await status.edit_text("🧠 Menganalisa...")
            
            t1 = time.time()
            llm_task = asyncio.create_task(moon_router.chat_async(request))
            moon_supervisor.register(llm_task)
            try:
                response = await llm_task
            except asyncio.CancelledError:
                await status.edit_text("⏹ Proses LLM dibatalkan.")
                return
            llm_time = time.time() - t1
            
            response_text, internal_log = policy_engine.evaluate(response.text)
            
            # Split Voice and Chat
            voice_match = re.search(r"\[VOICE\](.*?)\[/VOICE\]", response_text, flags=re.DOTALL | re.IGNORECASE)
            chat_match  = re.search(r"\[CHAT\](.*?)\[/CHAT\]", response_text, flags=re.DOTALL | re.IGNORECASE)

            spoken = voice_match.group(1).strip() if voice_match else response_text
            chat_text = chat_match.group(1).strip() if chat_match else response_text
            
            # Hard limit VOICE output to ~70 words to prevent runaway playbacks
            spoken_words = spoken.split()
            if len(spoken_words) > 70:
                spoken = " ".join(spoken_words[:70]) + "..."
            
            spoken = clean_for_tts(spoken)
                
            tts_time, play_time = 0.0, 0.0
            
            if len(spoken.strip()) < 5:
                await _reply_md(
                    status,
                    chat_text,
                    header="🎙️ Moon Voice\n━━━━━━━━━━━━━━━━━━━━\n💬 (Respons terlalu pendek, TTS dilewati)\n━━━━━━━━━━━━━━━━━━━━\n"
                )
            else:
                word_count = len(spoken.split())
                est_time = round(word_count / 2.5)
                
                if is_voice:
                    if voice_controller.stop_flag:
                        await status.edit("⏹ Proses dibatalkan oleh user.")
                        return

                    await status.edit(f"🎤 Menyiapkan suara... (Durasi sekitar {est_time} detik)")
                    
                    t2 = time.time()
                    filename = await _generate_tts(spoken)
                    tts_time = time.time() - t2
                    
                    header = (f"🎙️ Moon Voice\n━━━━━━━━━━━━━━━━━━━━\n"
                              f"🔊 Sedang berbicara... (Durasi sekitar {est_time} detik)\n━━━━━━━━━━━━━━━━━━━━\n")
                    await _reply_md(status, chat_text, header=header)
                    
                    t3 = time.time()
                    if voice_controller.stop_flag or voice_controller.muted:
                        if os.path.exists(filename): os.remove(filename)
                        await status.reply("🔇 Moon is muted or stopped. Playback skipped.")
                    else:
                        await _play_and_cleanup(chat_id, filename)
                    play_time = time.time() - t3
                else:
                    header = "🤖 Moon (Text Mode)\n━━━━━━━━━━━━━━━━━━━━\n"
                    await _reply_md(status, chat_text, header=header)
                    
            total_time = time.time() - overall_start
            
            voice_word_count = len(spoken.split())
            chat_word_count = len(chat_text.split())
            ocr_time_str = f"{ocr_time:.2f} s" if 'ocr_time' in locals() else "N/A"
            
            logger.info(
                f"\n━━━━━━━━━━━━━━━━━━\n"
                f"🌙 Moon Diagnostics\n\n"
                f"OCR        {ocr_time_str}\n"
                f"LLM       {llm_time:.2f} s\n\n"
                f"Output\n"
                f"VOICE : {voice_word_count} words\n"
                f"CHAT  : {chat_word_count} words\n\n"
                f"TTS        {tts_time:.2f} s\n"
                f"Playback  {play_time:.2f} s\n\n"
                f"Total     {total_time:.2f} s\n"
                f"━━━━━━━━━━━━━━━━━━\n"
            )

        except Exception as e:
            logger.error(f"process_request error: {e}")
            await status.edit_text(f"❌ Error: <pre>{html.escape(str(e))}</pre>")


@app.on_message(filters.command(["s", "stop"], prefixes="!") & (filters.me | filters.user(ALLOWED_USERS)))
async def stop_voice(client, message):
    chat_id = message.chat.id
    voice_controller.stop(chat_id)
    moon_supervisor.stop_flag = True
    for t in list(moon_supervisor.tasks):
        t.cancel()
    if is_voice_active(chat_id):
        try:
            await call_py.pause_stream(chat_id)
            await message.reply_text("⏹ Playback dan pipeline dibatalkan.")
        except Exception:
            pass

@app.on_message(filters.command(["mute"], prefixes="!") & (filters.me | filters.user(ALLOWED_USERS)))
async def mute_voice(client, message):
    voice_controller.mute()
    await message.reply_text("🔇 Moon Voice dimute. AI akan tetap membalas via chat, tapi TTS dimatikan.")

@app.on_message(filters.command(["unmute"], prefixes="!") & (filters.me | filters.user(ALLOWED_USERS)))
async def unmute_voice(client, message):
    voice_controller.unmute()
    await message.reply_text("🔊 Moon Voice di-unmute. TTS aktif kembali.")

@app.on_message(filters.command("tanya", prefixes="!") & (filters.me | filters.user(ALLOWED_USERS)))
async def handle_command_tanya(client, message):
    chat_id = message.chat.id
    raw_text = message.text or message.caption or ""
    if len(message.command) < 2 and not message.photo and not (message.reply_to_message and message.reply_to_message.photo):
        await message.reply_text("❌ Format: !tanya <pertanyaan> atau sertakan gambar")
        return
    user_text = raw_text.split(" ", 1)[1] if len(raw_text.split(" ")) > 1 else "Tolong analisa gambar ini"
    
    photo_to_analyze = None
    if message.reply_to_message and message.reply_to_message.photo:
        photo_to_analyze = message.reply_to_message.photo
    elif message.photo:
        photo_to_analyze = message.photo
        
    await process_request(client, message, chat_id, user_text, photo_to_analyze)

@app.on_message(filters.photo & (filters.me | filters.user(ALLOWED_USERS)))
async def handle_photo(client, message):
    chat_id = message.chat.id
    if not is_voice_active(chat_id):
        return
    user_text = message.caption or "Tolong analisa gambar ini"
    await process_request(client, message, chat_id, user_text, message.photo)

@app.on_message(filters.text & (filters.me | filters.user(ALLOWED_USERS)))
async def handle_text(client, message):
    chat_id = message.chat.id
    if not is_voice_active(chat_id):
        return
    raw_text = message.text or ""
    if raw_text.startswith("!"):
        return
    await process_request(client, message, chat_id, raw_text, None)


@app.on_message(filters.voice & (filters.me | filters.user(ALLOWED_USERS)))
async def voice_note_handler(client, message):
    """Voice Note handler: STT -> MoonAgent -> TTS"""
    chat_id = message.chat.id
    if not is_voice_active(chat_id):
        return
        
    user_id = str(message.from_user.id)
    name    = message.from_user.first_name or "Kapten"
    
    voice_controller.stop_flag = False
    
    try:
        await call_py.pause_stream(chat_id)
    except Exception:
        pass

    lock = _get_lock(chat_id)
    warning_msg = None
    if lock.locked():
        warning_msg = await message.reply_text("⏳ Bentar kapten, Moon masih dengerin VN sebelumnya...")

    async with lock:
        if warning_msg:
            try:
                await warning_msg.delete()
            except Exception:
                pass
                
        overall_start = time.time()
        status   = await message.reply_text("👂 Bentar, lagi dengerin VN lu...")
        ogg_path = None
        wav_path = None

        try:
            # 1. Download & Convert OGG -> WAV
            ogg_path = await message.download()
            wav_path = ogg_path + ".wav"
            audio = await asyncio.to_thread(AudioSegment.from_file, ogg_path, format="ogg")
            await asyncio.to_thread(audio.export, wav_path, format="wav")

            # 2. Offline STT (Faster Whisper)
            t0 = time.time()
            transcript = await asyncio.to_thread(_transcribe, wav_path)
            stt_time = time.time() - t0
            
            if not transcript:
                await status.edit_text("❌ Suara lu kosong atau kurang jelas kapten!")
                return

            await status.edit_text(
                f"🗣️ <b>Lu ngomong:</b> <i>{html.escape(transcript)}</i>\n\n🧠 Moon lagi mikir..."
            )

            # 3. Route to MoonAgent — voice is just a ChatRequest with input_type="voice"
            request = ChatRequest(
                module=Module.VOICE,
                platform_user_id=user_id,
                display_name=name,
                content=transcript,
                input_type="voice",
                intent="CHAT",
                extra_directive="[VOICE DIRECTIVE]: Ringkas, conversational, hindari markdown dan code blocks. Kalau ada command, bilang saja 'gue kirim kodenya di chat ya'."
            )
            
            t1 = time.time()
            llm_task = asyncio.create_task(moon_router.chat_async(request))
            moon_supervisor.register(llm_task)
            try:
                response = await llm_task
            except asyncio.CancelledError:
                await status.edit_text("⏹ Proses LLM dibatalkan.")
                return
            llm_time = time.time() - t1
            
            response_text, internal_log = policy_engine.evaluate(response.text)
            spoken   = clean_for_tts(response_text)
            
            tts_time, play_time = 0.0, 0.0
            if len(spoken.strip()) < 5:
                await status.edit_text(
                    f"🎙️ <b>Moon Voice</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 <b>Lu ngomong:</b> <code>{html.escape(transcript)}</code>\n\n"
                    f"💬 <i>(Respons terlalu pendek, TTS dilewati)</i>\n━━━━━━━━━━━━━━━━━━━━"
                )
            else:
                await status.edit_text(
                    f"🎙️ <b>Moon Voice</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 <b>Lu ngomong:</b> <code>{html.escape(transcript)}</code>\n\n"
                    f"🔊 Broadcasting...\n💬 <i>{html.escape(spoken)}</i>\n━━━━━━━━━━━━━━━━━━━━"
                )
                
                t2 = time.time()
                if voice_controller.stop_flag:
                    await status.edit_text("⏹ Proses dibatalkan oleh user.")
                    return
                filename = await _generate_tts(spoken)
                tts_time = time.time() - t2
                
                t3 = time.time()
                if voice_controller.stop_flag or voice_controller.muted:
                    if os.path.exists(filename): os.remove(filename)
                else:
                    await _play_and_cleanup(chat_id, filename)
                play_time = time.time() - t3
                
            total_time = time.time() - overall_start
            logger.info(
                f"\n━━━━━━━━━━━━━━━━━━━━\n"
                f"🌙 Moon Diagnostics (VN)\n"
                f"Prompt Tokens    : {response.prompt_tokens}\n"
                f"Completion Tokens: {response.completion_tokens}\n"
                f"STT Whisper      : {stt_time:.2f} s\n"
                f"LLM Generate     : {llm_time:.2f} s\n"
                f"TTS              : {tts_time:.2f} s\n"
                f"Playback         : {play_time:.2f} s\n"
                f"TOTAL            : {total_time:.2f} s\n"
                f"Retry Count      : {response.retry_count}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
            )

        except Exception as e:
            logger.error(f"Voice handler error: {e}")
            try:
                await status.edit_text(f"❌ Error: <pre>{html.escape(str(e))}</pre>")
            except MessageNotModified:
                pass
        finally:
            # Always clean up audio temp files
            for path in [ogg_path, wav_path]:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception as e:
                        logger.warning(f"Failed to cleanup {path}: {e}")


# =========================
# ENTRYPOINT (Kernel Supervisor)
# =========================
async def _disconnect_pytgcalls():
    logger.info("Disconnecting PyTgCalls...")
    try: await call_py.stop()
    except: pass
    try: await app.stop()
    except: pass

moon_supervisor.add_shutdown_hook(_disconnect_pytgcalls)
moon_supervisor.add_shutdown_hook(voice_controller.stop)

if __name__ == "__main__":
    logger.boot("🎙️ Moon Voice V3 — MoonAgent Pipeline initialized")
    logger.info(f"Model loaded: {settings.model_name}")
    logger.info(f"TTS Engine: {TTS_VOICE}")
    logger.info(f"Whisper Config: {WHISPER_MODEL} on {WHISPER_DEVICE}")
    logger.info("Session started. Kernel Supervisor Active. Press CTRL+C to stop gracefully.")
    
    moon_supervisor.install_signal()
    
    try:
        call_py.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Crash: {e}")
    finally:
        asyncio.get_event_loop().run_until_complete(moon_supervisor.shutdown())
        os._exit(0)
