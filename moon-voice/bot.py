import os
import asyncio
from pyrogram import Client, filters
import pyrogram.errors

from pytgcalls import PyTgCalls
from pytgcalls import idle
from pytgcalls.types import MediaStream, AudioQuality
import edge_tts
from dotenv import load_dotenv
from openai import AsyncOpenAI
import re
import speech_recognition as sr
from pydub import AudioSegment

env_path = os.path.join(os.path.dirname(__file__), "..", "moon-cli", ".env")
load_dotenv(env_path)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:1234/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "lm-studio")
MODEL_NAME = os.getenv("MODEL_NAME", "google/gemma-4-12b-qat")

llm_client = AsyncOpenAI(base_url=API_BASE_URL, api_key=OPENAI_API_KEY)

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

# Initialize Pyrogram and PyTgCalls
app = Client("moon_voice_session", api_id=API_ID, api_hash=API_HASH)
call_py = PyTgCalls(app)

# Voice Chat memory state
voice_memory = {}

def get_memory(chat_id):
    if chat_id not in voice_memory:
        voice_memory[chat_id] = []
    return voice_memory[chat_id]

def save_memory(chat_id, role, content):
    if chat_id not in voice_memory:
        voice_memory[chat_id] = []
    voice_memory[chat_id].append({"role": role, "content": content})
    voice_memory[chat_id].append({"role": role, "content": content})
    # Retain last 6 messages (3 interactions) to manage context window
    voice_memory[chat_id] = voice_memory[chat_id][-6:]

def get_system_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "moon-cli", "prompt", "system.md")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            base = f.read()
    except Exception:
        base = "You are Moon, an elite AI terminal assistant."
    return base + "\n\n[VOICE DIRECTIVE]: Jawab dengan bahasa gaul Indonesia (gue/lu), santai tapi teknis. Jangan terlalu panjang, maksimal 3 kalimat agar enak didengar lewat suara."

async def generate_tts(text, output_file="response.mp3"):
    print(f"🎙️ Generating TTS: {text}")
    communicate = edge_tts.Communicate(text, "id-ID-ArdiNeural")
    await communicate.save(output_file)
    print("✅ TTS Generated!")

@app.on_message(filters.command("join", prefixes="!"))
async def join_vc(client, message):
    chat_id = message.chat.id
    await message.reply_text("🔄 Menyambungkan ke Voice Chat...")
    
    try:
        # Generate welcome TTS stream
        await generate_tts("Halo Kapten, Moon Voice siap menerima perintah.")
        
        await call_py.play(
            chat_id,
            MediaStream(
                "response.mp3",
                audio_parameters=AudioQuality.HIGH
            )
        )
        await message.reply_text("✅ Berhasil masuk Voice Chat dan ngomong!")
    except Exception as e:
        await message.reply_text(f"❌ Gagal: {e}")

@app.on_message(filters.command("say", prefixes="!"))
async def say_vc(client, message):
    if len(message.command) < 2:
        return
    
    text = message.text.split(" ", 1)[1]
    chat_id = message.chat.id
    
    await message.reply_text(f"🗣️ Ngomong: {text}")
    await generate_tts(text, "response.mp3")
    
    try:
        await call_py.play(
            chat_id,
            MediaStream(
                "response.mp3",
                audio_parameters=AudioQuality.HIGH
            )
        )
    except Exception as e:
        await message.reply_text(f"❌ Gagal play: {e}")

def clean_for_tts(text):
    # Strip markdown symbols for natural TTS reading
    return re.sub(r'[\*\_\`#]', '', text).strip()

@app.on_message(filters.command("tanya", prefixes="!"))
async def tanya_vc(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ Teksnya mana bos? Format: !tanya <pertanyaan>")
        return
        
    prompt = message.text.split(" ", 1)[1]
    chat_id = message.chat.id
    
    await message.reply_text(f"🧠 Gemma lagi mikir: {prompt}...")
    
    try:
        # Prepare context memory
        history = get_memory(chat_id)
        messages = [{"role": "system", "content": get_system_prompt()}]
        messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        
        # Query LLM (Gemma)
        response = await llm_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages
        )
        ai_reply = response.choices[0].message.content
        
        # Save interaction to memory state
        save_memory(chat_id, "user", prompt)
        save_memory(chat_id, "assistant", ai_reply)
        
        # Clean response for TTS engine
        spoken_text = clean_for_tts(ai_reply)
        
        # Format Telegram UI output
        formatted_reply = (
            "🎙️ **Moon Voice System**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔊 **Status:** `Broadcasting Live...`\n"
            f"💬 **Transkrip:**\n_{spoken_text}_\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        
        await message.reply_text(formatted_reply)
        
        # Generate TTS and stream to Voice Chat
        await generate_tts(spoken_text, "response.mp3")
        
        await call_py.play(
            chat_id,
            MediaStream(
                "response.mp3",
                audio_parameters=AudioQuality.HIGH
            )
        )
    except Exception as e:
        await message.reply_text(f"❌ LLM Error: {e}")

@app.on_message(filters.voice)
async def voice_vc(client, message):
    chat_id = message.chat.id
    
    # Acknowledge incoming voice note
    status_msg = await message.reply_text("👂 Bentar, lagi dengerin VN lu...")
    
    try:
        # 1. Download Telegram OGG file
        file_path = await message.download()
        
        # 2. Convert OGG to WAV using pydub
        wav_path = file_path + ".wav"
        audio = AudioSegment.from_file(file_path, format="ogg")
        audio.export(wav_path, format="wav")
        
        # 3. Speech-to-Text (STT) processing
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text_result = recognizer.recognize_google(audio_data, language="id-ID")
            
        await status_msg.edit_text(f"🗣️ Lu ngomong: *{text_result}*\n\n🧠 Gemma lagi mikir...")
        
        # Cleanup temporary audio files
        os.remove(file_path)
        os.remove(wav_path)
        
        # Prepare context memory
        history = get_memory(chat_id)
        messages = [{"role": "system", "content": get_system_prompt()}]
        messages.extend(history)
        messages.append({"role": "user", "content": text_result})
        
        # Query LLM (Gemma)
        response = await llm_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages
        )
        ai_reply = response.choices[0].message.content
        
        # Save interaction to memory state
        save_memory(chat_id, "user", text_result)
        save_memory(chat_id, "assistant", ai_reply)
        
        # Clean response for TTS engine
        spoken_text = clean_for_tts(ai_reply)
        
        # Format Telegram UI output
        formatted_reply = (
            "🎙️ **Moon Voice System**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Lu ngomong:** `{text_result}`\n\n"
            "🔊 **Status:** `Broadcasting Live...`\n"
            f"💬 **Transkrip:**\n_{spoken_text}_\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        
        await status_msg.edit_text(formatted_reply)
        
        # Generate TTS and stream to Voice Chat
        await generate_tts(spoken_text, "response.mp3")
        
        await call_py.play(
            chat_id,
            MediaStream(
                "response.mp3",
                audio_parameters=AudioQuality.HIGH
            )
        )
        
    except sr.UnknownValueError:
        await status_msg.edit_text("❌ Suara lu kurang jelas kapten, Gemma nggak bisa denger!")
    except Exception as e:
        await status_msg.edit_text(f"❌ Error Pas Proses Suara: {e}")

@app.on_message(filters.command("leave", prefixes="!"))
async def leave_vc(client, message):
    chat_id = message.chat.id
    try:
        await call_py.leave_call(chat_id)
        await message.reply_text("👋 Udah keluar dari Voice Chat.")
    except Exception as e:
        await message.reply_text(f"❌ Gagal keluar: {e}")

import threading
import sys
import subprocess
import signal
import os

def force_kill():
    if os.name == 'nt':
        subprocess.call(['taskkill', '/F', '/T', '/PID', str(os.getpid())])
    else:
        os.kill(os.getpid(), signal.SIGKILL)

def console_listener():
    while True:
        try:
            cmd = input()
            if cmd.strip().lower() in ['quit', 'exit', 'stop']:
                print("🌙 Shutting down Moon Voice Bot (Brute Force)...")
                force_kill()
        except (EOFError, KeyboardInterrupt):
            force_kill()

print("="*50)
print("🎙️ Moon Voice Bot (PyTgCalls Engine)")
print("STATUS : ACTIVE")
print("DEV    : iMoon")
print("="*50)
print("Ketik 'quit' untuk stop dengan aman.\n")

threading.Thread(target=console_listener, daemon=True).start()

call_py.start()
idle()
