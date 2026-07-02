import time
import sys
from enum import Enum


class LogLevel(Enum):
    BOOT = 0
    INFO = 1
    DEBUG = 2
    WARN = 3
    ERROR = 4


class MoonLogger:
    def __init__(self, level=LogLevel.INFO):
        self.level = level

    def _should_log(self, level):
        return level.value >= self.level.value

    def _log(self, level, msg):
        if not self._should_log(level):
            return

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level.name}] {msg}")

    def boot(self, msg):
        self._log(LogLevel.BOOT, msg)

    def info(self, msg):
        self._log(LogLevel.INFO, msg)

    def debug(self, msg):
        self._log(LogLevel.DEBUG, msg)

    def warn(self, msg):
        self._log(LogLevel.WARN, msg)

    def error(self, msg):
        self._log(LogLevel.ERROR, msg)

# Default global instance
logger = MoonLogger(level=LogLevel.INFO)
