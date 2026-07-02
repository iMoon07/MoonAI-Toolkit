import time
import sys
from enum import Enum


class LogLevel(Enum):
    TRACE = -1
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

    def trace_task(self, task_id, task_name, state, details=""):
        """
        Forensic trace for asyncio lifecycles.
        Writes unconditionally to moon_trace.log.
        """
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{state}] [{task_id}] {task_name}"
        if details:
            log_entry += f" - {details}"
            
        with open("moon_trace.log", "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

# Default global instance
logger = MoonLogger(level=LogLevel.INFO)
