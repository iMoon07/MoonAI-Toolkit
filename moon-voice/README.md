# 🎙️ moon-voice

This module is responsible for bridging the MoonAI Toolkit with Telegram Voice Chats using a Pyrogram Userbot and PyTgCalls.

## Features

- Joins active Telegram Voice Chats.
- Allows users to query the AI via text commands and receives responses via synthesized speech (TTS) directly in the Voice Chat.
- (Experimental) Handles incoming Voice Notes using Speech-to-Text (STT) for hands-free interactions.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration**:
   Copy `.env.example` to `.env` (or configure via your main toolkit `.env`) and add your credentials:
   - `API_ID` & `API_HASH` (from my.telegram.org)
   - Note: The first time you run this, Pyrogram will ask you to log in with your phone number to generate a `.session` file. **Never commit your `.session` file.**

3. **Run**:
   ```bash
   python bot.py
   ```

## Usage

In any group where the Userbot is present and a Voice Chat is active:
- `!join` - Summon the bot into the Voice Chat.
- `!tanya [text]` - Ask a question. The bot will process it locally and speak the answer.
- `!leave` - Dismiss the bot from the Voice Chat.
