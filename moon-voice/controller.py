import asyncio
from typing import Optional

class VoiceController:
    def __init__(self):
        self.muted = False
        self.stop_flag = False

    def stop(self, chat_id: Optional[int] = None):
        self.stop_flag = True

    def mute(self):
        self.muted = True

    def unmute(self):
        self.muted = False

    def reset(self):
        self.stop_flag = False

# Global instance for the voice bot
voice_controller = VoiceController()
