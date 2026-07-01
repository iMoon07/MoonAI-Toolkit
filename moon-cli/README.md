# 🛠️ moon-cli

This is the core orchestration layer of the MoonAI Toolkit. It handles the personality configuration, system prompts, and the core connection to the local LLM.

## Structure
- `cli.py` & `main.py`: Entry points for running the local conversational loop.
- `llm/`: Contains the logic for context management, HTTP API communication, and response parsing.
- `prompt/`: Holds `system.md` which defines the persona and strict behavioral bounds of the AI assistant.
- `.env`: Environment file containing connection parameters to LM Studio, as well as tokens for the Telegram bots.

## Setup
1. Configure your `.env` file. Ensure `API_BASE_URL` points to your local LM Studio server. Add your Telegram tokens if you plan to use `moon-bot` or `moon-voice`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the CLI directly:
   ```bash
   python main.py
   ```
