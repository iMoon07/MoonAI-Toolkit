# MoonAI Toolkit 🌙

<p align="center">
  <img src="skull-hacking-time-4k-rh-2048x1152.jpg" alt="MoonAI Toolkit" width="100%" />
</p>

MoonAI Toolkit is a modular, locally hosted AI assistant. It is designed for cybersecurity engineers to chat, troubleshoot issues, and interact directly via Telegram.



🎥 **Video Demo & Tutorial:** [Watch on YouTube](https://www.youtube.com/watch?v=nlhn60OoRW8)

📖 **Full Documentation on the Blog:** [Build Your Assistant AI: Moon Toolkit](https://imoon07.github.io/read.html?post=moonai-toolkit&lang=en)

**100% Private.** All processing is done locally on your machine. No data is sent to external servers.

## Architecture Overview

```text
Moon toolkit
│
├── moon-cli                # Core AI Engine & Configuration
│   ├── .env                # API Keys and Telegram tokens
│   ├── cli.py              # Command-line interface logic
│   ├── main.py             # Main entry script for CLI
│   ├── requirements.txt    # CLI dependencies
│   ├── README.md           # CLI documentation
│   ├── llm/                # AI logic (memory, routing)
│   └── prompt/             # AI system prompts
│
├── moon-bot                # Telegram Text & Vision Bot
│   ├── bot.py              # Main bot execution script
│   ├── config.py           # Bot configuration settings
│   ├── requirements.txt    # Bot dependencies
│   └── core/               # Core bot handlers
│
└── moon-voice              # Telegram Voice Chat Assistant
    ├── bot.py              # Voice assistant runner
    ├── main.py             # Audio processing (STT & TTS)
    └── requirements.txt    # Voice dependencies
```

## Prerequisites

1. **LM Studio**: Must be running locally on port `1234`. (Recommended model: `gemma-4-12b-qat`).
2. **Python**: Version 3.10 or higher.
3. **Telegram Accounts**: A Bot Token (from BotFather) and an API ID/Hash (for Voice Chat).

## Quick Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/iMoon07/MoonAI-Toolkit.git
   cd MoonAI-Toolkit
   ```

2. **Configure Environment (.env):**
   Go to the `moon-cli` folder, edit the `.env` file, and add your credentials:
   - `BOT_TOKEN`: Required to run `moon-bot` (Text).
   - `API_ID` & `API_HASH`: Required if you want to use `moon-voice` (Voice).

3. **Run the Text Bot (Terminal 1):**
   ```bash
   cd moon-bot
   pip install -r requirements.txt
   python bot.py
   ```

4. **Run the Voice Bot (Terminal 2):**
   ```bash
   cd moon-voice
   pip install -r requirements.txt
   python bot.py
   ```

> **Disclaimer:** This tool is strictly for educational and research purposes. Use at your own risk.
