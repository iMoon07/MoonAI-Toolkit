# Moon History (Pre-Git Era)

This document tracks the conceptual evolution of the MoonAI Toolkit from its inception (V1.0) up to V1.5. These versions existed before rigorous Git version control was established and represent the "Conceptual Phase" of Moon's architecture.

---

## V1.0 - The Monolith
- Moon started as a simple Telegram AI.
- Architecture consisted of a single, massive system prompt.
- No conversational memory or context retention.

## V1.3 - State Management
- **Problem**: Voice mode and Telegram bots were colliding.
- **Decision**: Introduced cross-process `shared_state.json`.
- **Result**: Implemented Secretary Mode and Voice Interruption handling.

## V1.4 - Vision Pipeline
- **Problem**: Vision analysis was hardcoded and rigid.
- **Decision**: Built a `VisionPipeline` abstraction.
- **Result**: Tesseract OCR performance was empirically benchmarked; switching OCR engines became modular.

## V1.5 - Runtime Router & Context Composer
- **Problem**: The system prompt became too large and impossible to debug.
- **Decision**: Replaced `PromptManager` with `ContextComposer` and built the `MoonRouter`.
- **Result**: Prompts became modular and dynamic based on user intent tags.

## V1.5.1 - Cognitive Stack (The Turning Point)
- **Problem**: The legacy `base.md` file still had too many overlapping responsibilities (Reasoning, Identity, Tone).
- **Decision**: Completely dismantled `base.md` into the 6-Layer Cognitive Stack (`Identity`, `Reasoning`, `Conversation`, `Response`, `Style`, `Intent`).
- **Result**: Clean separation of concerns. This state marks the baseline where proper Git version control officially begins.
