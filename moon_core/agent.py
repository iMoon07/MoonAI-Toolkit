import re
import time
from typing import AsyncGenerator, Generator

from moon_core.memory import memory_store
from moon_core.client import MoonClient
from moon_core.context import context_composer
from moon_core.logger import logger
from moon_core.models import ChatRequest, ChatResponse, MoonContext

class MoonAgent:
    """
    Central Orchestrator for the MoonAI Toolkit.
    Takes a ChatRequest, builds the MoonContext, and executes the AI pipeline.
    """
    def __init__(self):
        self.memory = memory_store
        self.context = context_composer
        self.client = MoonClient()

    def _ensure_session(self, request: ChatRequest) -> tuple[str, str]:
        user_id = self.memory.get_or_create_user(request.module.value, request.platform_user_id, request.display_name)
        session_id = self.memory.get_last_session(user_id, request.module.value)
        if not session_id:
            session_id = self.memory.create_session(user_id, request.module.value, title=f"New {request.module.value.capitalize()} Session")
        return user_id, session_id

    def clear_context(self, request: ChatRequest):
        """Wipes the message history for the current session."""
        _, session_id = self._ensure_session(request)
        self.memory.clear_session(session_id)

    def _build_context(self, request: ChatRequest) -> MoonContext:
        """Gathers persistent facts, session summaries, and raw history to build the context."""
        user_id, session_id = self._ensure_session(request)
        
        # 1. Context Composition
        system_content = self.context.build(
            intent_result=request.intent, 
            module_name=request.module.value, 
            extra_directive=request.extra_directive
        )

        # 2. Inject Persistent Facts
        facts = self.memory.load_facts(user_id=user_id)
        if facts:
            facts_str = "\n".join([f"- {k}: {v}" for k, v in facts.items()])
            system_content += f"\n\n[USER FACTS]\n{facts_str}"

        # 3. Inject Session Summary & History
        mem_context = self.memory.get_session_context(session_id=session_id)
        if mem_context["summary"]:
            system_content += f"\n\n[SESSION SUMMARY]\n{mem_context['summary']}"

        # 4. Construct Final Message Array
        messages = [{"role": "system", "content": system_content}]
        for msg in mem_context["messages"]:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        # Add the current user request to the context so LLM can see it
        messages.append({"role": "user", "content": request.content})
            
        return MoonContext(
            request=request,
            user_id=user_id,
            session_id=session_id,
            history=mem_context["messages"],
            facts=facts,
            summary=mem_context["summary"],
            messages=messages
        )

    def _stabilize_output(self, text: str) -> str:
        """Strips <think> blocks before saving to memory."""
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'<think>.*', '', text, flags=re.DOTALL)
        return text.strip()

    def _save_response(self, context: MoonContext, raw_response: str, latency_ms: int = 0) -> ChatResponse:
        """Stabilizes and commits the final output to SQLite, returning a ChatResponse."""
        final_response = self._stabilize_output(raw_response)
        
        self.memory.append(
            session_id=context.session_id, 
            role="assistant", 
            content=final_response,
            input_type="text",
            model=self.client.model,
            temperature=self.client.temperature,
            latency_ms=latency_ms
        )
        
        return ChatResponse(
            text=final_response,
            session_id=context.session_id,
            token_usage=0,  # Token estimation can be added later
            latency_ms=latency_ms,
            model=self.client.model
        )

    # ==========================
    # CLI (Synchronous Stream)
    # ==========================
    def chat_stream(self, request: ChatRequest) -> Generator[str, None, None]:
        context = self._build_context(request)
        
        # Append User Message
        self.memory.append(
            context.session_id, 
            role="user", 
            content=request.content, 
            input_type=request.input_type
        )
        
        start_time = time.time()
        try:
            stream = self.client.stream(context.messages)
            full_response = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    full_response += delta
                    yield delta
                    
            latency_ms = int((time.time() - start_time) * 1000)
            self._save_response(context, full_response, latency_ms)
            
        except Exception as e:
            logger.error(f"Agent stream error: {e}")
            self.memory.rollback(context.session_id)
            raise

    # ==========================
    # Bot/Voice (Async Complete)
    # ==========================
    async def chat_async(self, request: ChatRequest) -> ChatResponse:
        context = self._build_context(request)
        
        # Append User Message
        self.memory.append(
            context.session_id, 
            role="user", 
            content=request.content, 
            input_type=request.input_type
        )
        
        start_time = time.time()
        max_retries = 1
        retries = 0
        response_text = ""
        p_tokens, c_tokens = 0, 0
        
        while retries <= max_retries:
            try:
                response_text, p_tokens, c_tokens = await self.client.chat(context.messages)
                
                # Response Guard
                if response_text and response_text.strip():
                    break
                    
                logger.warning(f"Empty LLM response. Retrying {retries+1}/{max_retries}...")
                retries += 1
            except Exception as e:
                logger.error(f"Agent async error: {e}")
                self.memory.rollback(context.session_id)
                raise
                
        latency_ms = int((time.time() - start_time) * 1000)
        
        # History Guard: only save to SQLite if response is valid
        if response_text and response_text.strip():
            final_response = self._save_response(context, response_text, latency_ms)
        else:
            final_response = ChatResponse(
                text="", 
                session_id=context.session_id, 
                latency_ms=latency_ms, 
                model=self.client.model
            )
            
        final_response.prompt_tokens = p_tokens
        final_response.completion_tokens = c_tokens
        final_response.retry_count = retries
        return final_response


# Global MoonAgent Service
moon_agent = MoonAgent()
