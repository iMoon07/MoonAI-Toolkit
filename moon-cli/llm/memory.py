import os

class Memory:
    def __init__(self, system_prompt):
        self.system = system_prompt
        self.messages = []
        self.max_history = 10

    def add(self, role, content):
        self.messages.append({"role": role, "content": content})
        self.trim()

    def trim(self):
        # Clean Version: Only keep the last 10 messages to prevent noise and memory hallucinations
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]

    def build(self):
        return [{"role": "system", "content": self.system}] + self.messages

    def reset(self):
        self.messages = []
