# 💬 moon-bot

The standard Telegram Text & Vision Bot module for the MoonAI Toolkit. It functions as a terminal assistant accessible directly from your Telegram client, deeply integrated with your local LM Studio and cybersecurity workflows.

## Features

- **Text Engine** — Uses the same global `system.md` prompt as Moon CLI, ensuring consistent reasoning across the terminal, Telegram, and voice interfaces.
- **Vision Engine** — Analyzes screenshots, error logs, and terminal outputs via the abstracted `VisionPipeline`.
- **Secretary Mode (One Reply Policy)** — Avoids API collisions by reading `shared_state.json`. If `moon-voice` is currently active in the chat, `moon-bot` silently skips processing.

## Architecture

This module has been fully migrated to the `moon_core` MoonRouter pipeline. It is now a **thin UI wrapper** — all LLM logic, memory, and prompt management are handled by `moon_core`.

### 🧠 LLM Memory & MoonRouter Orchestration
- `moon-bot` no longer manages any LLM logic. It constructs a `ChatRequest` and awaits `moon_core.runtime.router.MoonRouter`.
- Fully integrated into the global `moon_memory.db` SQLite backend (WAL mode, thread-safe).

### 🛡️ State Management & Rate Limiting
- Uses dedicated limiter classes (`RateLimiter`, `SlidingWindowLimiter`, and `BanManager`) to isolate user state.
- Utilizes `moon_core.state` to respect cross-process active Voice Modes.

### 👁️ Asynchronous Vision (OCR)
- Vision parsing relies on the `VisionPipeline` in `moon_core.vision`.
- Tesseract (or future alternatives) is offloaded to `asyncio.to_thread()` (non-blocking).
- After OCR, the extracted text is passed to `MoonRouter` via `ChatRequest(input_type="vision")`.

### ⚡ Graceful Error Handling & UX
- Wrapped all Local LLM API calls in a strict 120-second `asyncio.wait_for` timeout.
- Implemented granular error mapping for `APIConnectionError`, `RateLimitError`, and `TimeoutError` so users know exactly why a request failed without exposing internal stack traces.

## Requirements

- Python 3.11+
- LM Studio (or a compatible OpenAI-format local API server)
- Telegram Bot Token
- Tesseract OCR *(Optional, required for Vision capabilities)*

## Installation

1. Clone the toolkit repository.
2. Ensure your `.env` file (configured in the `moon-cli` directory) has your `BOT_TOKEN` and `ALLOWED_USERS` securely set.
3. Install dependencies:
   ```bash
   pip install -e . # Ensure the root moon_core package is installed
   pip install -r moon-bot/requirements.txt
   ```
4. Run the bot:
   ```bash
   python bot.py
   ```

## Architecture Layout

```text
moon-bot/
├── bot.py           # Thin UI wrapper — Telegram handlers only
├── README.md        # Documentation
└── core/            
    ├── identity.py  # /help text and footer
    ├── limiter.py   # RateLimiter, SlidingWindow, BanManager
    └── vision.py    # Legacy vision helpers
```
