import os
import json
from pathlib import Path
from filelock import FileLock

# We store the state in a simple JSON file in the moon_core directory
STATE_FILE = os.path.join(os.path.dirname(__file__), "shared_state.json")
LOCK_FILE = STATE_FILE + ".lock"

def _load_state():
    if not os.path.exists(STATE_FILE):
        return {"voice_mode_chats": []}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
    except (json.JSONDecodeError, FileNotFoundError):
        # Be specific with exceptions. If file is corrupt or gone, return a default state.
        return {"voice_mode_chats": []}

def _save_state(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)
    # Atomic write: write to a temporary file first, then rename.
    # This prevents file corruption if the process crashes during write.
    temp_file = STATE_FILE + ".tmp"
    with open(temp_file, "w") as f:
        json.dump(data, f, indent=4)
    os.replace(temp_file, STATE_FILE)

def set_voice_active(chat_id: int):
    state = _load_state()
    if chat_id not in state["voice_mode_chats"]:
        state["voice_mode_chats"].append(chat_id)
        _save_state(state)
    with FileLock(LOCK_FILE):
        state = _load_state()
        if chat_id not in state["voice_mode_chats"]:
            state["voice_mode_chats"].append(chat_id)
            _save_state(state)

def set_voice_inactive(chat_id: int):
    state = _load_state()
    if chat_id in state["voice_mode_chats"]:
        state["voice_mode_chats"].remove(chat_id)
        _save_state(state)
    with FileLock(LOCK_FILE):
        state = _load_state()
        if chat_id in state["voice_mode_chats"]:
            state["voice_mode_chats"].remove(chat_id)
            _save_state(state)

def is_voice_active(chat_id: int) -> bool:
    state = _load_state()
    return chat_id in state["voice_mode_chats"]
    with FileLock(LOCK_FILE):
        state = _load_state()
        return chat_id in state["voice_mode_chats"]
