import os
from typing import List
from dotenv import load_dotenv
from moon_core.models import IntentResult

load_dotenv()

class IntentClassifier:
    """
    Classifies the user's intent to determine the appropriate response style and tags.
    Returns an IntentResult containing primary and secondary intents.
    """
    def __init__(self):
        self.threshold = int(os.getenv("INTENT_DEEP_DIVE_THRESHOLD", "2"))

    def detect(self, text: str, input_type: str = "text") -> IntentResult:
        """Heuristic classifier for user intents."""
        text_lower = text.lower().strip()
        
        # 1. Vision overrides
        if input_type == "vision" or input_type == "image":
            return IntentResult(primary="VISION", secondary=[])
            
        # 2. Greeting / Fast bypassing
        greetings = {"halo", "hai", "hi", "yo", "p", "bro", "bang", "kapten", "test", "tes"}
        # Clean punctuation to get actual words
        clean_text = text_lower.replace("?", "").replace("!", "").replace(".", "").replace(",", "")
        words = set(clean_text.split())
        
        if text_lower in greetings or (len(words) <= 3 and bool(words & greetings)):
            return IntentResult(primary="GREETING", secondary=[])
            
        acks = {"ok", "oke", "sip", "mantap", "thanks", "makasih", "thank you", "siap"}
        if text_lower in acks or (len(words) <= 3 and bool(words & acks)):
            return IntentResult(primary="GREETING", secondary=[])

        # 3. Detect specialized tags
        tags = set()
        
        debug_kws = ["error", "bug", "traceback", "crash", "gagal", "fail", "macet", "stuck", "exception"]
        if any(kw in text_lower for kw in debug_kws):
            tags.add("DEBUG")
            
        sec_kws = ["exploit", "cve", "log", "siem", "bypass", "vuln", "xss", "sqli", "nmap", "recon", "malware", "hardening", "forensic"]
        if any(kw in text_lower for kw in sec_kws):
            tags.add("SECURITY")
            
        code_kws = ["code", "script", "python", "bash", "review", "refactor", "snippet", "function", "class", "algoritma"]
        if any(kw in text_lower for kw in code_kws):
            tags.add("CODING")
            
        deep_kws = ["jelaskan", "bedah", "analisis", "analisa", "kupas", "elaborate", "detail"]
        if any(kw in text_lower for kw in deep_kws):
            tags.add("DEBUG")
            
        # 4. Resolve Primary and Secondary
        if not tags:
            return IntentResult(primary="CHAT", secondary=[])
            
        tags_list = list(tags)
        
        if "SECURITY" in tags_list:
            primary = "SECURITY"
        elif "DEBUG" in tags_list:
            primary = "DEBUG"
        elif "CODING" in tags_list:
            primary = "CODING"
        else:
            primary = tags_list[0]
            
        secondary = [t for t in tags_list if t != primary]
        
        return IntentResult(primary=primary, secondary=secondary)

# Global singleton
intent_classifier = IntentClassifier()
