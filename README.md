# MoonAI Toolkit 🌙

<p align="center">
  <img src="skull-hacking-time-4k-rh-2048x1152.jpg" alt="MoonAI Toolkit" width="100%" />
</p>

MoonAI Toolkit is a modular, locally hosted AI Runtime. It is designed for cybersecurity engineers to chat, troubleshoot issues, and interact directly via Terminal and Telegram.

🎥 **Video Demo & Tutorial:** [Watch on YouTube](https://www.youtube.com/watch?v=nlhn60OoRW8)

📖 **Full Documentation on the Blog:** [Build Your Assistant AI: Moon Toolkit](https://imoon07.github.io/read.html?post=moonai-toolkit&lang=en)

---

## Why Moon?

Unlike cloud AI assistants, Moon runs entirely on your own hardware.

- **100% Private**: No internet dependency for reasoning. No data leaves your machine.
- **Context-Aware**: Shares memory across Telegram, Voice, and Terminal sessions.
- **Cybersecurity Focused**: Prompt boundaries are strictly tailored for offensive/defensive analysis.
- **Fully Modular Architecture**: Swap out OCR engines, LLM backends, or add new UI frontends seamlessly via the `moon_core` framework.

## Features

- 💬 **Local LLM Chat** — Seamless integration with LM Studio.
- 🖼️ **OCR & Vision Analysis** — Extract and analyze logs/code from screenshots.
- 🎙️ **Telegram Voice Assistant** — Hands-free audio chat with local STT and TTS.
- 🧠 **Shared Memory Engine** — SQLite-backed cross-platform conversational memory and persistent facts.
- 🛡️ **Conversation Style Control** — Dynamic heuristic intent routing to adapt tone from casual chats to deep engineering dives.
- 🛠️ **Developer Benchmark Tools** — Built-in scripts to empirically test vision pipelines.

---

## Architecture Overview

```text
          Telegram
             │
             ▼
      moon-bot / moon-voice / CLI
             │
             ▼
          MoonAgent
             │
 ┌───────────┼────────────┐
 │           │            │
 ▼           ▼            ▼
Vision     Memory  Cognitive Stack
 │           │      (6-Layer OS)
 └───────────┼────────────┘
             ▼
        MoonClient
             ▼
      LM Studio (Gemma)
```

```text
MoonAI-Toolkit/
│
├── setup.py                # Installs moon_core as an editable package
├── .env                    # Global API Keys, Telegram tokens, and Tuning values
│
├── tools/                  # 🛠️ Developer & Benchmarking Tools
│   ├── benchmark_ocr.py    
│   └── benchmark_opencv.py 
│
├── moon_core/              # 🧠 The Unified Brain
│   ├── models.py           # Core Data Objects (ChatRequest, ChatResponse, MoonContext)
│   ├── agent.py            # Central Orchestrator Pipeline
│   ├── client.py           # Unified Sync/Async LLM Router
│   ├── memory.py           # MemoryStore Service (SQLite DB: moon_memory.db)
│   ├── prompt.py           # Layered Prompt Builder
│   ├── intent.py           # ML-ready IntentClassifier Heuristics
│   ├── vision.py           # VisionPipeline and Abstract VisionEngines
│   ├── state.py            # Cross-process shared JSON state manager
│   └── logger.py           # Standardized Observability
│
├── moon-cli/               # 🛠️ Terminal Assistant
│   ├── main.py             # CLI Entry Point
│   └── prompt/             # Base System Persona Rules
│
├── moon-bot/               # 💬 Telegram Text & Vision Bot
│   ├── bot.py              # Main bot execution script
│   └── core/               # Vision & Router Handlers
│
└── moon-voice/             # 🎙️ Telegram Voice Assistant
    └── bot.py              # Audio processing (STT & TTS)
```

## Prerequisites

1. **LM Studio**: Must be running locally on port `1234`. (Recommended model: `gemma-4-12b-qat`).
2. **Python**: Version 3.11 or higher.
3. **Telegram Accounts**: A Bot Token (from BotFather) and an API ID/Hash (for Voice Chat).

## Quick Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/iMoon07/MoonAI-Toolkit.git
   cd MoonAI-Toolkit
   ```

2. **Configure Environment (.env):**
   Create a `.env` file at the root of the project:
   - `OPENAI_API_KEY`, `API_BASE_URL`, `MODEL_NAME` (Required for LLM)
   - `BOT_TOKEN`: Required for `moon-bot` (Text).
   - `API_ID` & `API_HASH`: Required for `moon-voice` (Voice).
   - `OCR_PSM`, `OCR_BENCHMARK_PSMS`: Optional Tesseract configs.
   - `INTENT_DEEP_DIVE_THRESHOLD`: (Default: 2) Magic number for deep-dive conversation style.

3. **Install Core Framework:**
   ```bash
   pip install -e .
   ```

4. **Run any Module:**
   - CLI: `cd moon-cli && python main.py`
   - Telegram Bot: `cd moon-bot && python bot.py`
   - Voice Bot: `cd moon-voice && python bot.py`

---

## Roadmap

- [x] Unified `moon_core` framework
- [x] Telegram Voice Integration
- [x] OCR Pipeline Abstraction & Benchmark
- [x] V1.5: Runtime Router & Context Composer
- [x] V1.5.1: Modular Cognitive Stack Refactor (6-Layer Architecture)
- [ ] V1.6: Execution Stack MVP (Capability Registry, Pragmatic Providers, Permission Middleware, Scheduler)
- [ ] V1.7: Workspace Manager (OS, repo, and environment awareness)
- [ ] V1.8: Activity Logger (Passive terminal/VSCode journaling)
- [ ] V1.9: Planner (Multi-step reasoning and autonomous execution)
- [ ] V2.0: AI Runtime Engine (End-to-end framework agnostic to LLM backends)

> **See [CHANGELOG.md](CHANGELOG.md) for detailed version history.**

> **Disclaimer:** This tool is strictly for educational and research purposes. Use at your own risk.
