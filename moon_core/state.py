import os
import json
from pathlib import Path

# We store the state in a simple JSON file in the moon_core directory
STATE_FILE = os.path.join(os.path.dirname(__file__), "shared_state.json")

def _load_state():
    if not os.path.exists(STATE_FILE):
        return {"voice_mode_chats": []}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"voice_mode_chats": []}

def _save_state(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)

def set_voice_active(chat_id: int):
    state = _load_state()
    if chat_id not in state["voice_mode_chats"]:
        state["voice_mode_chats"].append(chat_id)
        _save_state(state)

def set_voice_inactive(chat_id: int):
    state = _load_state()
    if chat_id in state["voice_mode_chats"]:
        state["voice_mode_chats"].remove(chat_id)
        _save_state(state)

def is_voice_active(chat_id: int) -> bool:
    state = _load_state()
    return chat_id in state["voice_mode_chats"]
