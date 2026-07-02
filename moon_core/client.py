import asyncio
from openai import OpenAI, AsyncOpenAI, APIConnectionError, RateLimitError, APIError
from moon_core.config import settings
from moon_core.logger import logger
from moon_core.exceptions import APITimeoutError

class MoonClient:
    """
    Unified LLM Client providing both sync (CLI) and async (Bot/Voice) interfaces.
    Enforces standardized timeouts, retries, and temperatures.
    """
    def __init__(self):
        self.model = settings.model_name
        self.temperature = settings.temperature
        
        # Initialize both clients internally
        self._sync_client = OpenAI(
            base_url=settings.api_base_url,
            api_key=settings.openai_api_key
        )
        self._async_client = AsyncOpenAI(
            base_url=settings.api_base_url,
            api_key=settings.openai_api_key
        )

    def stream(self, messages: list[dict]):
        """Synchronous streaming specifically for the CLI."""
        try:
            return self._sync_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                stream=True
            )
        except Exception as e:
            logger.error(f"Sync stream error: {e}")
            raise

    async def chat(self, messages: list[dict], timeout: float = 120.0) -> tuple[str, int, int]:
        """Asynchronous complete response for Telegram Bots & Voice."""
        try:
            coro = self._async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature
            )
            response = await asyncio.wait_for(coro, timeout=timeout)
            
            content = response.choices[0].message.content or ""
            prompt_tokens = response.usage.prompt_tokens if getattr(response, "usage", None) else 0
            completion_tokens = response.usage.completion_tokens if getattr(response, "usage", None) else 0
            
            return content, prompt_tokens, completion_tokens
            
        except asyncio.TimeoutError:
            logger.error(f"API Timeout ({timeout}s)")
            raise APITimeoutError("Model failed to respond within the timeout period.")
        except Exception as e:
            logger.error(f"Async chat error: {e}")
            raise
