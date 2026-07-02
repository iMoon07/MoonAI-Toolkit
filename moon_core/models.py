from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List

class Module(Enum):
    CLI = "cli"
    TELEGRAM = "telegram"
    VOICE = "voice"
    WEB = "web"

@dataclass
class IntentResult:
    primary: str
    secondary: List[str] = field(default_factory=list)

@dataclass
class ChatRequest:
    module: Module
    platform_user_id: str
    display_name: str
    content: str
    input_type: str = "text"  # 'text', 'vision', 'voice'
    intent: IntentResult = field(default_factory=lambda: IntentResult("CHAT"))
    extra_directive: str = ""
    metadata: Dict = field(default_factory=dict)

@dataclass
class MoonContext:
    request: ChatRequest
    user_id: str
    session_id: str
    history: List[Dict] = field(default_factory=list)
    facts: Dict = field(default_factory=dict)
    summary: Optional[str] = None
    messages: List[Dict] = field(default_factory=list)

@dataclass
class ChatResponse:
    text: str
    session_id: str
    token_usage: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    retry_count: int = 0
    latency_ms: int = 0
    model: str = ""
