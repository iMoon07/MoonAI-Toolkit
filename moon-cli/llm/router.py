def route_input(text: str) -> tuple[str, str]:
    text = text.lower()

    # 1. Detect Intent
    intent = "CHAT"
    if any(k in text for k in ["error", "traceback", "bug", "crash", "failed"]):
        intent = "DEBUG"
    elif any(k in text for k in ["build", "create", "buat", "bikin", "script"]):
        intent = "BUILD"
    elif any(k in text for k in ["explain", "how", "why", "kenapa", "jelasin"]):
        intent = "LEARN"

    # 2. Detect Mood
    mood = "CASUAL"
    if any(k in text for k in ["anjing", "bangsat", "kesel", "gila", "babi", "tai", "tolol"]):
        mood = "ANGRY"
    elif any(k in text for k in ["wkwk", "haha", "lol", "canda", "hehe"]):
        mood = "JOKE"
    elif intent in ["DEBUG", "BUILD"] or len(text) > 50:
        # If coding or long technical text, automatically switch to serious
        mood = "SERIOUS"

    return intent, mood
