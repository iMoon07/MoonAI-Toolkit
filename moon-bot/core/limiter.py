import time
from collections import deque

class RateLimiter:
    def __init__(self, cooldown=2.0):
        self.cooldown = cooldown
        self.user_last = {}

    def check(self, uid):
        now = time.time()
        last_time = self.user_last.get(uid, 0)
        
        if now - last_time < self.cooldown:
            wait_time = self.cooldown - (now - last_time)
            return False, wait_time
            
        self.user_last[uid] = now
        self._cleanup(now)
        return True, 0.0
        
    def _cleanup(self, now):
        # Prune users inactive for 10x the cooldown to prevent memory leak
        expired = [u for u, t in self.user_last.items() if now - t > self.cooldown * 10]
        for u in expired:
            del self.user_last[u]

class SlidingWindowLimiter:
    def __init__(self, window=60.0, limit=5):
        self.window = window
        self.limit = limit
        self.history = {}

    def check(self, uid):
        now = time.time()
        
        if uid not in self.history:
            self.history[uid] = deque()
            
        q = self.history[uid]

        # Pop expired timestamps
        while q and now - q[0] > self.window:
            q.popleft()

        if len(q) >= self.limit:
            wait_time = self.window - (now - q[0])
            return False, wait_time

        q.append(now)
        self._cleanup(now)
        return True, 0.0

    def _cleanup(self, now):
        # Remove uids entirely if their queue is empty
        empty = [u for u, q in self.history.items() if not q or now - q[-1] > self.window]
        for u in empty:
            del self.history[u]

class BanManager:
    def __init__(self):
        self.banned = {}

    def is_banned(self, uid):
        now = time.time()
        if uid in self.banned:
            if now < self.banned[uid]:
                return True
            del self.banned[uid]
        self._cleanup(now)
        return False

    def temp_ban(self, uid, sec=30):
        self.banned[uid] = time.time() + sec

    def _cleanup(self, now):
        expired = [u for u, t in self.banned.items() if now > t]
        for u in expired:
            del self.banned[u]

# Instantiate globally for the bot
rate_limiter = RateLimiter(cooldown=2.0)
image_limiter = SlidingWindowLimiter(window=60.0, limit=5)
ban_manager = BanManager()
