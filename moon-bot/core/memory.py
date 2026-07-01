memory = {}

def get(uid):
    return memory.get(uid, [])

def push(uid, role, content):
    memory.setdefault(uid, []).append({
        "role": role,
        "content": content
    })

    # Keep only last 10 interactions to avoid memory bloat
    memory[uid] = memory[uid][-10:]
