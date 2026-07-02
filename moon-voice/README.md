# 🎙️ moon-voice

The Telegram Voice Userbot for the MoonAI Toolkit. This module allows you to hold hands-free, low-latency audio conversations with Moon using Telegram Voice Notes. It leverages `faster-whisper` for offline Speech-to-Text (STT) and `edge-tts` for Text-to-Speech.

## Architecture

This module is now a **thin UI wrapper**. STT and TTS remain local in `bot.py` as pre/post-processing steps. All LLM, Memory, Prompt, and Style logic is routed through `moon_core.runtime.router.MoonRouter`.

- **Unified Memory**: Uses `moon_memory.db` via `moon_core`. 
- **Unified Agent Pipeline**: Transcribed text is wrapped in `ChatRequest(input_type="voice")` and passed to `MoonRouter`.
- **Shared State (`moon_core.state`)**: Broadcasts Voice Mode active status to `shared_state.json` so `moon-bot` can gracefully mute itself (One Reply Policy).
- **Dynamic Context Control**: Passes transcribed voice text to `MoonRouter`, which dynamically injects casual conversation guidelines unless the user explicitly requests a technical deep dive.

### UX and Observability Upgrades
- **Kernel Supervisor**: All execution is governed by `moon_core.supervisor`, featuring a 4-Stage Graceful Shutdown Pipeline and a global 10s watchdog to prevent zombies on `CTRL+C`.
- **Split Voice/Chat Pipeline**: LLM output is parsed into a short `[VOICE]` summary for TTS and a detailed `[CHAT]` markdown response sent as text.
- **Application-Level Enforcement**: The Python pipeline actively truncates Voice outputs to a maximum of 70 words to prevent runaway 2-minute LLM playbacks.
- **Queue UX & Race Conditions**: If a user spams messages, an `asyncio.Lock` queues the requests and notifies the user with a temporary wait message.
- **Instant Interruption**: Send `!s` or `!stop` to instantly kill TTS playback and clear the audio queue using `VoiceController` and `MoonSupervisor`.
- **Manual Trigger (`!tanya`)**: Voice logic is cleanly separated from manual query commands, preventing logic duplication when querying without entering full Voice Mode.

## Setup

1. **Configure Environment**
   Edit the `.env` file at the root of `MoonAI-Toolkit`. You will need your Telegram `API_ID` and `API_HASH` in addition to the standard LM Studio config.
2. **Install Dependencies**
   ```bash
   pip install -e ..
   pip install -r requirements.txt
   ```
3. **Generate Session**
   First, run the login helper to generate the `.session` file (you will be prompted to log in to Telegram via your phone number):
   ```bash
   python main.py
   ```
4. **Run the Voice Bot**
   ```bash
   python bot.py
   ```

## Workflow
1. User sends a Voice Note to the Userbot.
2. `pyrogram` downloads the OGG file.
3. `pydub` converts OGG to WAV.
4. `faster-whisper` transcribes the WAV offline locally.
5. `ChatRequest(input_type="voice")` is sent to `moon_core.runtime.router.MoonRouter`.
6. MoonRouter bypasses if it's a simple greeting, otherwise passes to MoonAgent which loads facts + history from `moon_memory.db`, analyzes intent via `IntentClassifier` and `ContextComposer`, queries LM Studio, and saves the response.
7. `clean_for_tts()` strips markdown/code blocks from the response.
8. `edge-tts` generates an MP3 file.
9. `pyrogram` plays the MP3 in Voice Chat and uploads it back as a Voice Note.
10. All temporary files (`.ogg`, `.wav`, `.mp3`) are cleaned up in `finally:` blocks.
