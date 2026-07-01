import html
import os
import re
from openai import AsyncOpenAI
from core.memory import get, push
from config import API_BASE_URL, OPENAI_API_KEY, MODEL_NAME

# Initialize OpenAI Async Client pointing to LM Studio
client = AsyncOpenAI(
    base_url=API_BASE_URL,
    api_key=OPENAI_API_KEY
)

def build_prompt(intent, text):
    # Load system prompt rules from moon-cli system.md for absolute consistency
    base_dir = os.path.dirname(os.path.abspath(__file__))
    system_prompt_path = os.path.join(base_dir, "..", "..", "moon-cli", "prompt", "system.md")
    try:
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            base_system = f.read()
    except Exception as e:
        base_system = "You are Moon, an AI cybersecurity assistant."
    
    # Append routing behavior based on intent
    if intent == "DEBUG":
        base_system += "\n\n[ROUTER DIRECTIVE]: The user is reporting an error or bug. Focus heavily on Root Cause -> Mechanism -> Actionable Fixes."
    elif intent == "SECURITY":
        base_system += "\n\n[ROUTER DIRECTIVE]: The user is asking about a security concept, log, or scan. Focus strictly on defensive cybersecurity analysis."
    
    return base_system

def parse_markdown_to_telegram(text):
    """Converts standard LLM markdown to Telegram's strict HTML format."""
    # First, escape HTML to avoid tag collision
    text = html.escape(text)
    
    # 1. Parse Code Blocks ```lang \n code \n ```
    text = re.sub(r'```(?:[a-zA-Z0-9]+)?\n(.*?)\n```', r'<pre>\1</pre>', text, flags=re.DOTALL)
    text = re.sub(r'```(.*?)```', r'<pre>\1</pre>', text, flags=re.DOTALL)
    
    # 2. Parse Inline Code `code`
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # 3. Parse Bold **text**
    text = re.sub(r'\*\*([^\*]+)\*\*', r'<b>\1</b>', text)
    
    # 4. Parse Italic *text* (Ignore leading spaces to preserve bullet points)
    text = re.sub(r'(?<!\*)\*([^\*\n]+)\*(?!\*)', r'<i>\1</i>', text)
    text = re.sub(r'\b_([^_]+)_\b', r'<i>\1</i>', text)
    
    # 5. Parse Headings (### Heading -> Bold)
    text = re.sub(r'^###\s+(.*)', r'<b>\1</b>', text, flags=re.MULTILINE)
    text = re.sub(r'^##\s+(.*)', r'<b>\1</b>', text, flags=re.MULTILINE)
    text = re.sub(r'^#\s+(.*)', r'<b>\1</b>', text, flags=re.MULTILINE)
    
    # 6. Parse Markdown bullet points to literal bullet characters
    text = re.sub(r'^[\*\-]\s+', '• ', text, flags=re.MULTILINE)
    
    return text

async def generate_response(text, intent, uid):
    history = get(uid)
    system_prompt = build_prompt(intent, text)
    
    # Construct message array
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add history
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    # Add current user text
    messages.append({"role": "user", "content": text})
    
    # Call Local LLM via LM Studio
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
        )
        ai_reply = response.choices[0].message.content
        
        # Parse the Markdown output from AI into Telegram HTML
        final_output = parse_markdown_to_telegram(ai_reply)
        
    except Exception as e:
        final_output = f"⚠️ <b>Engine Error:</b> <pre>{str(e)}</pre>"

    push(uid, "user", text)
    push(uid, "assistant", final_output)

    return final_output
