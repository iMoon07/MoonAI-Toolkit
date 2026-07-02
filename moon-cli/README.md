# 🛠️ moon-cli

The terminal-based interactive chat interface for the MoonAI Toolkit. It provides a raw, engineering-focused connection to your local LLM (via LM Studio), running directly in your console.

## Architecture

`moon-cli` consumes the `moon_core` foundation library. It acts purely as a standard I/O shell.

### Key Features
- **Thin UI Wrapper**: The CLI constructs a `ChatRequest` and streams the response via `moon_core.runtime.router.MoonRouter`.
- **Shared Memory**: Connects to the global `moon_memory.db` SQLite database via `moon_core`. If you restart the CLI, it can automatically resume your last active session.
- **Cross-Platform Facts**: Learns persistent facts about your environment (e.g., favorite OS, active projects) and shares this context intelligently with the Telegram Bot and Voice Bot.
- **Unified Client**: Relies on `MoonClient` for standardized API connections, timeout handling, and strict token limits.
- **Dynamic Context**: Powered by `moon_core.runtime.router`, it automatically detects your intent and dynamically builds the prompt modules (Base, Debug, Coding, Security) via `ContextComposer`.

## Setup

1. Configure your `.env` file at the root of the toolkit. Ensure `API_BASE_URL` points to your local LM Studio server.
2. Install dependencies (ensuring the editable `moon_core` package is installed):
   ```bash
   pip install -e ..
   pip install -r requirements.txt
   ```
3. Run the CLI directly:
   ```bash
   python main.py
   ```

## Structure
- `cli.py` & `main.py`: Entry points for running the local conversational loop.
