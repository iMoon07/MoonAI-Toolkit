import os
from dataclasses import dataclass
from dotenv import load_dotenv, find_dotenv
from typing import Optional
from moon_core.exceptions import ConfigurationError

# Auto-locate and load .env from anywhere in the tree (starts from moon_core and goes up to root)
load_dotenv(find_dotenv())

@dataclass
class MoonSettings:
    # LLM Settings
    api_base_url: str
    openai_api_key: str
    model_name: str
    temperature: float = 0.2
    
    # Telegram Bot Settings (Optional for CLI-only)
    bot_token: Optional[str] = None
    allowed_users: list[str] = None

    # Vision Settings (Optional)
    tesseract_path: Optional[str] = None

    @classmethod
    def load(cls) -> "MoonSettings":
        api_base = os.getenv("API_BASE_URL")
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("MODEL_NAME")

        if not api_base or not api_key or not model:
            raise ConfigurationError(
                "Missing core LLM configuration. Ensure API_BASE_URL, OPENAI_API_KEY, and MODEL_NAME are set in .env"
            )
            
        allowed_users_raw = os.getenv("ALLOWED_USERS", "")
        allowed_users = [u.strip() for u in allowed_users_raw.split(",")] if allowed_users_raw else []

        return cls(
            api_base_url=api_base,
            openai_api_key=api_key,
            model_name=model,
            temperature=float(os.getenv("TEMPERATURE", "0.2")),
            bot_token=os.getenv("BOT_TOKEN"),
            allowed_users=allowed_users,
            tesseract_path=os.getenv("TESSERACT_PATH")
        )

# Global singleton configuration
settings = MoonSettings.load()
