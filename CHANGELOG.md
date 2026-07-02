# Changelog

All notable changes to the MoonAI Toolkit will be documented in this file.

## [V1.5.1] - Modular Cognitive Stack Refactor
- **Separation of Concerns**: Completely dismantled the remaining prompt monoliths into a 6-Layer Cognitive Stack (`Identity`, `Reasoning`, `Conversation`, `Response`, `Style`, `Intent`).
- **Style Enum**: Introduced `SpeakingStyle` (NORMAL, FORMAL, TECHNICAL) in `moon_core/style.py` decoupled from reasoning logic to prevent persona contamination.
- **ContextComposer Upgrade**: The prompt pipeline now strictly sequences the cognitive layers to provide deterministic and highly debuggable AI behavior.
- **Cleanup**: Deleted the legacy `base.md` completely.

## [V1.5] - Runtime Router & Context Composer
- **AI Runtime Transformation**: Moon is transitioning from a traditional chatbot (single massive prompt) to an AI Runtime.
- **IntentResult Classification**: Upgraded `IntentClassifier` to return an `IntentResult` containing multiple tags (e.g., `primary: SECURITY`, `secondary: [CODING]`).
- **Modular Prompts**: Discarded the monolithic `system.md`. Split rules into modular blocks (`base.md`, `debug.md`, `security.md`, `coding.md`).
- **ContextComposer (`moon_core/context.py`)**: Replaced `PromptManager`. Dynamically builds context by composing only the necessary modules based on Intent tags.
- **MoonRouter (`moon_core/runtime/router.py`)**: The new control plane. Handles `GREETING` bypasses (0 token, 0 ms latency using a random greeting pool) and routes complex intents to `MoonAgent`.

## [V1.4.1] - Conversation Style Control
- **IntentClassifier (`moon_core/intent.py`)**: To combat "Personality Drift" (where the bot acts like a professor instead of a casual assistant), a heuristic scoring system evaluates user input. Unless analytical triggers (`bedah`, `analisis`, `jelaskan`) are detected, the bot is injected with a `[CONVERSATION DIRECTIVE]` forcing it to keep responses short, casual, and free of unnecessary engineering analogies.

## [V1.4] - Observability & OCR Benchmarking
- **Data-Driven Engineering**: Replaced random library swapping with concrete metrics. Introduced `benchmark_ocr.py` and `benchmark_opencv.py` (now in `tools/`) to test various OpenCV pipelines (CLAHE, Otsu, Adaptive Threshold) against different Tesseract PSMs.
- **VisionPipeline Abstraction**: `moon_core/vision.py` was refactored into a `VisionPipeline` abstraction layer that accepts `VisionEngine` implementations. Switching from Tesseract to EasyOCR or a Vision LLM no longer requires altering bot handlers.

## [V1.3] - State Management & UX Cleanup
- **One Reply Policy (Secretary Mode)**: Introduced `shared_state.json` via `moon_core/state.py`. When `moon-voice` enters active Voice Mode in a Telegram group, `moon-bot` detects this state and intelligently silences itself to prevent LLM processing collisions.
- **Voice Interruption UX**: Playback via `edge-tts` can be immediately terminated using the `!stop` command.
