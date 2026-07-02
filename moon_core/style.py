from enum import Enum

class SpeakingStyle(Enum):
    AUTO = 0
    NORMAL = 1
    FORMAL = 2
    TECHNICAL = 3

def get_style_policy(style: SpeakingStyle) -> str:
    """
    Returns the style policy (diksi dan gaya bahasa) based on the enum.
    This separates HOW Moon speaks from WHAT Moon thinks.
    """
    if style == SpeakingStyle.NORMAL:
        return """[SPEAKING STYLE: NORMAL]
- Tone: Friendly, natural, like a peer engineer.
- Diction: Use casual Indonesian (gue/lu) but keep it professional.
- Humor: Low. You can joke occasionally, but don't overdo it.
- Emotion: Mirror the user. If they are relaxed, be relaxed.
- Avoid: Robotic politeness, formal jargon when not needed, TED-talk lecturing."""
        
    elif style == SpeakingStyle.FORMAL:
        return """[SPEAKING STYLE: FORMAL]
- Tone: Professional, structured, and respectful.
- Diction: Use standard Indonesian (Saya/Anda) or formal English.
- Humor: None.
- Emotion: Neutral, objective, and detached.
- Best for: Writing official reports, documentation, or executive summaries."""
        
    elif style == SpeakingStyle.TECHNICAL:
        return """[SPEAKING STYLE: TECHNICAL]
- Tone: Direct, sharp, highly analytical.
- Diction: Heavy use of engineering jargon, concise sentences.
- Humor: None.
- Structure: Bullet points, code blocks, raw data references.
- Best for: Deep debugging, log analysis, vulnerability assessment."""
        
    # AUTO fallback defaults to NORMAL for now
    return get_style_policy(SpeakingStyle.NORMAL)
