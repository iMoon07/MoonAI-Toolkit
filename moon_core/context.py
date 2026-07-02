import os
from moon_core.logger import logger
from moon_core.intent import IntentResult
from moon_core.style import SpeakingStyle, get_style_policy

class ContextComposer:
    """
    Dynamically builds context by composing the 6-Layer Architecture:
    Identity -> Reasoning -> Conversation -> Response -> Style -> Intent.
    """
    def __init__(self):
        self.prompts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
        self.modules = {}
        self._load_all_modules()

    def _load_all_modules(self):
        # The core 4 layers and the intent modules
        files = ["identity.md", "reasoning.md", "conversation.md", "response.md", 
                 "debug.md", "coding.md", "security.md"]
        for file in files:
            path = os.path.join(self.prompts_dir, file)
            try:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        name = file.replace(".md", "")
                        self.modules[name] = f.read().strip()
                else:
                    self.modules[file.replace(".md", "")] = ""
            except Exception as e:
                logger.error(f"Failed to load prompt module {file}: {e}")
                self.modules[file.replace(".md", "")] = ""
                
        # Ensure identity exists
        if not self.modules.get("identity"):
            self.modules["identity"] = "You are Moon, an AI assistant."

    def build(self, intent_result: IntentResult, style: SpeakingStyle = SpeakingStyle.NORMAL, module_name: str = "cli", extra_directive: str = "") -> str:
        """
        Composes the final prompt layered in the 6-layer architecture.
        """
        parts = []
        
        # 1. Identity Layer
        if self.modules.get("identity"):
            parts.append(self.modules["identity"])
            
        # 2. Reasoning Layer
        if self.modules.get("reasoning"):
            parts.append(self.modules["reasoning"])
            
        # 3. Conversation Layer
        if self.modules.get("conversation"):
            parts.append(self.modules["conversation"])
            
        # 4. Response Layer
        if self.modules.get("response"):
            parts.append(self.modules["response"])
            
        # 5. Speaking Style Layer
        parts.append(get_style_policy(style))
        
        # 6. Intent Modules
        # Add primary tag prompt if exists
        primary_lower = intent_result.primary.lower()
        if primary_lower in self.modules and self.modules[primary_lower]:
            parts.append(self.modules[primary_lower])
            
        # Add secondary tags prompts
        for sec in intent_result.secondary:
            sec_lower = sec.lower()
            if sec_lower in self.modules and self.modules[sec_lower]:
                parts.append(self.modules[sec_lower])
        
        # Additional Overrides (Vision / Voice / Custom)
        if module_name == "vision":
            parts.append("[VISION DIRECTIVE]\nYou are analyzing an image via OCR. Use OCR text as primary evidence.")
        elif module_name == "voice":
            parts.append("[VOICE DIRECTIVE]\nYou are speaking via Voice Chat. Keep responses conversational and brief. NO code blocks.")

        if extra_directive:
            parts.append(f"[CUSTOM DIRECTIVE]\n{extra_directive}")

        return "\n\n".join(parts)

# Global singleton
context_composer = ContextComposer()
