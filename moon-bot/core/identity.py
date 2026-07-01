from config import DEV_NAME, LINKEDIN, WEBSITE

def footer():
    return f"\n\n—\n<b>Moon CLI</b> • Developed by {DEV_NAME}"

def get_help_text():
    return f"""⚡ <b>Moon CLI / Help</b>

<b>CORE COMMANDS:</b>
• /start - Start bot session
• /help - Show command list

<b>CAPABILITIES:</b>
• <b>AppSec & Cloud Architecture:</b> Secure SDLC, Web/API Sec, IAM, Cloud Posture, and Cryptography.
• <b>Offensive & Defensive Ops:</b> Architecture, Red/Blue/Purple Teaming, Threat Intel, and Exploit Dev.
• <b>Endpoint, DFIR & Malware:</b> OS Internals, Digital Forensics, Incident Response, and Reverse Engineering.
• <b>Code, Hardware & OT:</b> Python/C/ASM Scripting, IoT/Embedded Sec, SCADA/ICS, and Debugging.

<b>VOICE CHAT INTEGRATION (Moon Voice):</b>
• <code>!join</code> - Summon Moon into active Voice Chat
• <code>!tanya [text]</code> - Ask Moon a question (Voice reply)
• <code>!leave</code> - Dismiss Moon from Voice Chat
• 🎤 <b>Voice Note:</b> Send a voice message and Moon will reply via Voice Chat!

<i>Moon CLI is a terminal-grade AI assistant designed for engineering workflows.</i>
"""
