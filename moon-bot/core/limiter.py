import time
from collections import defaultdict, deque

user_last = {}
banned = {}
img_hist = defaultdict(deque)

COOLDOWN = 2.0


def rate_limit(uid):
    now = time.time()
    if now - user_last.get(uid, 0) < COOLDOWN:
        return False
    user_last[uid] = now
    return True


def is_banned(uid):
    if uid in banned:
        if time.time() < banned[uid]:
            return True
        del banned[uid]
    return False


def temp_ban(uid, sec=30):
    banned[uid] = time.time() + sec


def image_limit(uid):
    now = time.time()
    q = img_hist[uid]

    while q and now - q[0] > 60:
        q.popleft()

    if len(q) >= 5:
        return False

    q.append(now)
    return True
