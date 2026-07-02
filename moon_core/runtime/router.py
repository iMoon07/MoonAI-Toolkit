import os
import random
from typing import Generator
from moon_core.models import ChatRequest, ChatResponse
from moon_core.intent import intent_classifier
from moon_core.agent import moon_agent

class GreetingHandler:
    """Handles fast, 0-token bypassing for greetings to preserve personality."""
    def __init__(self):
        self.pool = [
            "Yo 👋, ada yang mau dibahas?",
            "Gue standby, Kapten.",
            "Halo. Lanjut ngoprek?",
            "Siap laksanakan.",
            "Yo Raja, aman?",
            "Aman, bro. Gas.",
            "Halo! Ada error atau log yang mau dianalisa?"
        ]
        
    def get_reply(self) -> str:
        return random.choice(self.pool)

class MoonRouter:
    """
    The main control plane for Moon. 
    Routes input -> Intent -> Context -> Agent, or bypasses LLM entirely.
    """
    def __init__(self):
        self.greeting = GreetingHandler()
        self.agent = moon_agent
        
    def _create_fast_response(self, request: ChatRequest, text: str) -> ChatResponse:
        """Saves interaction to memory and returns a 0-latency ChatResponse."""
        from moon_core.memory import memory_store
        user_id, session_id = self.agent._ensure_session(request)
        
        # Append to memory so the session stays coherent
        memory_store.append(session_id, "user", request.content, request.input_type)
        memory_store.append(session_id, "assistant", text, "text", model="router_bypass")
        
        return ChatResponse(
            text=text,
            session_id=session_id,
            latency_ms=0,
            model="router_bypass"
        )
        
    async def chat_async(self, request: ChatRequest) -> ChatResponse:
        # 1. Classify Intent
        intent_result = intent_classifier.detect(request.content, request.input_type)
        request.intent = intent_result
        
        # 2. Bypass / Fast Handlers
        if intent_result.primary == "GREETING":
            return self._create_fast_response(request, self.greeting.get_reply())
            
        # 3. Forward to Agent
        return await self.agent.chat_async(request)
        
    def chat_stream(self, request: ChatRequest) -> Generator[str, None, None]:
        # 1. Classify Intent
        intent_result = intent_classifier.detect(request.content, request.input_type)
        request.intent = intent_result
        
        # 2. Bypass / Fast Handlers
        if intent_result.primary == "GREETING":
            reply = self.greeting.get_reply()
            self._create_fast_response(request, reply)
            yield reply
            return
            
        # 3. Forward to Agent stream
        yield from self.agent.chat_stream(request)
        
    def clear_context(self, request: ChatRequest):
        self.agent.clear_context(request)

# Global singleton
moon_router = MoonRouter()
