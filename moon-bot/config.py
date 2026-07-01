import os
from dotenv import load_dotenv

# Load .env dari folder moon-cli (karena token dan config LM Studio ada di sana)
env_path = os.path.join(os.path.dirname(__file__), "..", "moon-cli", ".env")
load_dotenv(env_path)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:1234/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "lm-studio")
MODEL_NAME = os.getenv("MODEL_NAME", "google/gemma-4-12b-qat")

DEV_NAME = "iMoon"
LINKEDIN = "https://www.linkedin.com/in/imoon07"
WEBSITE = "https://imoon07.github.io/about.html"

# Security Zone: Hanya ID di bawah ini yang bisa pakai bot. Kalau kosong, semua orang bisa pakai.
_allowed = os.getenv("ALLOWED_USERS", "")
ALLOWED_USERS = [u.strip() for u in _allowed.split(",") if u.strip()]
