# 💬 moon-bot

The standard Telegram Text & Vision Bot module for the MoonAI Toolkit. It functions as a terminal assistant accessible directly from your Telegram client.

## Features
- Provides intelligent answers to text queries based on the `moon-cli` backend configuration.
- Includes Vision (OCR) capabilities to read and analyze screenshots, error logs, and terminal outputs.

## Setup
1. Ensure your `.env` file (configured in the `moon-cli` directory) has your `BOT_TOKEN` and `ALLOWED_USERS` securely set.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the bot:
   ```bash
   python bot.py
   ```
