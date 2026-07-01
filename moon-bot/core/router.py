def detect_intent(text: str):
    t = text.lower()

    if any(x in t for x in ["error", "bug", "trace", "crash"]):
        return "DEBUG"

    if any(x in t for x in ["buat", "code", "script", "build"]):
        return "BUILD"

    if any(x in t for x in ["scan", "packet", "log", "forensic"]):
        return "SECURITY"

    return "CHAT"
