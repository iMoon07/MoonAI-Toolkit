import html
import os
import pytesseract
from PIL import Image
from openai import AsyncOpenAI
from config import API_BASE_URL, OPENAI_API_KEY, MODEL_NAME

# Setup path Tesseract untuk Windows (default instalasi)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

client = AsyncOpenAI(
    base_url=API_BASE_URL,
    api_key=OPENAI_API_KEY
)

async def analyze_image(path, caption):
    try:
        # Ekstrak tulisan dari gambar secara lokal pakai Tesseract OCR
        with Image.open(path) as img:
            extracted_text = pytesseract.image_to_string(img)
            
        if not extracted_text.strip():
            extracted_text = "[TIDAK ADA TEKS YANG BISA DIBACA DI GAMBAR INI]"
            
        # Load system prompt rules from moon-cli system.md
        system_prompt_path = os.path.join(os.path.dirname(__file__), "..", "..", "moon-cli", "prompt", "system.md")
        try:
            with open(system_prompt_path, "r", encoding="utf-8") as f:
                base_system = f.read()
        except Exception:
            base_system = "You are Moon, an AI cybersecurity assistant."
            
        base_system += "\n\n[VISION DIRECTIVE]: The user has uploaded an image and its text content was extracted via OCR. Analyze the extracted text (especially if it contains code, errors, or logs) and provide actionable insights."

        # Kita jadikan ini CHAT TEKS BIASA ke Gemma, Gemma ngga tau ini gambar
        user_message = f"Caption dari user: {caption if caption else 'Tolong analisa error log ini.'}\n\nHasil Ekstraksi Teks (OCR) dari Gambar:\n```text\n{extracted_text}\n```"
        
        messages = [
            {"role": "system", "content": base_system},
            {"role": "user", "content": user_message}
        ]
        
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
        )
        
        ai_reply = response.choices[0].message.content
        safe_reply = html.escape(ai_reply)
        return f"<b>[OCR SCAN]</b>\n\n{safe_reply}"
        
    except Exception as e:
        return f"⚠️ <b>OCR Engine Error:</b> <pre>{str(e)}</pre>"
