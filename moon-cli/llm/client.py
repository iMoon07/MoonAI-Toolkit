from openai import OpenAI
import os

class MoonLLM:
    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("API_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = os.getenv("MODEL_NAME")



    def stream(self, messages):
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True
        )
