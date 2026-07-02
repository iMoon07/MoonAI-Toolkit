import re
import json
from typing import Tuple, Dict, Any, Optional
from moon_core.logger import logger

class PolicyEngine:
    def evaluate(self, raw_text: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Evaluates LLM output, extracts JSON (Execution Layer), 
        enforces Confidence Guard, and returns clean Markdown for the User Layer.
        """
        internal_log = None
        clean_text = raw_text

        # 1. Extract JSON block if it exists
        json_match = re.search(r"```json\s*(.*?)\s*```", raw_text, flags=re.DOTALL | re.IGNORECASE)
        if json_match:
            try:
                internal_log = json.loads(json_match.group(1))
                # Remove JSON from the user-facing text
                clean_text = raw_text.replace(json_match.group(0), "").strip()
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from LLM output.")

        # 2. Confidence Guard (Hard Rule)
        if internal_log and isinstance(internal_log, dict):
            confidence = internal_log.get("confidence")
            try:
                conf_val = float(confidence) if confidence is not None else 1.0
                if conf_val < 0.6:
                    logger.warning(f"Policy Engine Intervention: Confidence {conf_val} < 0.6. Aborting deep analysis.")
                    # Force override output to prevent hallucination
                    clean_text = "[VOICE]Data tidak cukup jelas, Kapten.[/VOICE]\n[CHAT]⚠️ **Policy Guard: Data is insufficient.**\nResolusi gambar terlalu rendah atau data log tidak lengkap untuk analisis yang akurat. Mohon perjelas input Anda.[/CHAT]"
                    return clean_text, internal_log
            except ValueError:
                pass

        # 3. Structured Markdown Injection (if JSON was present but no Markdown provided)
        # This ensures the user still sees the finding if the LLM only outputted JSON
        if internal_log and not re.search(r"\[CHAT\](.*?)\[/CHAT\]", clean_text, flags=re.DOTALL | re.IGNORECASE):
            md_append = "\n[CHAT]\n⚠️ **Analysis Result**\n"
            for k, v in internal_log.items():
                if k.lower() != "confidence":
                    md_append += f"- **{k.capitalize()}**: {v}\n"
            md_append += "[/CHAT]"
            # Also ensure voice exists
            if "[VOICE]" not in clean_text:
                clean_text = "[VOICE]Analisis selesai. Gue kirim detailnya di chat ya.[/VOICE]\n" + md_append
            else:
                clean_text += md_append

        return clean_text, internal_log

# Global singleton
policy_engine = PolicyEngine()
