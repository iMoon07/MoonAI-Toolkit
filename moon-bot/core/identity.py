from dotenv import load_dotenv
import os

load_dotenv()

DEV_NAME = os.getenv("DEV_NAME", "iMoon")
WEBSITE  = os.getenv("WEBSITE", "https://imoon07.github.io")
LINKEDIN = os.getenv("LINKEDIN", "https://linkedin.com")

def footer() -> str:
    return f"\n\n—\n<b>Moon</b> • Developed by {DEV_NAME}"

def get_help_text() -> str:
    return """<b>Moon</b>

<b>Commands</b>
• /start - Start Moon
• /help  - Show this menu

<b>Voice Commands (Userbot)</b>
• !join  - Join active Voice Chat
• !tanya [text] - Ask Moon in VC
• !leave - Leave Voice Chat
• !stop / !s - Stop Moon's audio and generation instantly
• !mute  - Mute Moon's voice (text only mode)
• !unmute - Unmute Moon's voice

<b>Text Chat</b>
Send any message — Moon will respond via the MoonAgent pipeline.

<b>Vision</b>
Send a screenshot or image — Moon will OCR it and analyze the content.

<b>Voice Note</b>
Send a voice note — Moon transcribes and replies with audio.

<i>Moon is designed for debugging, cybersecurity, software engineering, and system analysis.</i>
"""
