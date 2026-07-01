def stabilize_output(text: str) -> str:
    """
    Force AI output to be clean and terminal-friendly.
    """

    # Remove empty noise
    text = text.strip()

    # Split safety
    import re
    # Remove markdown bold (**) and italic (*)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'\1', text)

    lines = text.strip().split("\n")
    cleaned = []
    
    for line in lines:
        if not line.strip():
            continue
        # Ignore think blocks
        if "<think>" in line or "</think>" in line:
            continue
        cleaned.append(line)

    # Limit wild lengths
    if len(cleaned) > 50:
        cleaned = cleaned[:50]
        cleaned.append("... (truncated)")

    return "\n".join(cleaned)
