import sqlite3
import os
import uuid
import threading
from typing import List, Dict, Optional
from datetime import datetime
from moon_core.logger import logger
from moon_core.exceptions import MoonCoreException

class DatabaseError(MoonCoreException):
    """Raised when an SQLite database operation fails."""
    pass

# Determine the toolkit root directory based on the location of this file
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DB_PATH = os.path.join(ROOT_DIR, "moon_memory.db")

class MemoryStore:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()  # Thread-safe writes for CLI+Bot+Voice
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        # WAL mode: allows concurrent reads while a single writer is active.
        # Critical for CLI + Bot + Voice running simultaneously.
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _execute(self, query: str, params: tuple = (), commit: bool = True):
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute(query, params)
                    if commit:
                        conn.commit()
                    return cursor.fetchall()
            except sqlite3.Error as e:
                logger.error(f"Database error on query {query}: {e}")
                raise DatabaseError(f"Database operation failed: {e}")

    def _init_db(self):
        """Initialize the schema for Moon Memory with indexes and soft deletes."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.executescript("""
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        platform TEXT,
                        platform_user_id TEXT,
                        display_name TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(platform, platform_user_id)
                    );

                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        user_id TEXT REFERENCES users(id),
                        module TEXT,
                        title TEXT,
                        summary TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS messages (
                        -- Use rowid implicitly for absolute chronological sorting
                        id TEXT PRIMARY KEY,
                        session_id TEXT REFERENCES sessions(id),
                        role TEXT,
                        content TEXT,
                        input_type TEXT,
                        token_estimate INTEGER,
                        model TEXT,
                        temperature REAL,
                        latency_ms INTEGER,
                        deleted INTEGER DEFAULT 0,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS facts (
                        id TEXT PRIMARY KEY,
                        user_id TEXT REFERENCES users(id),
                        key TEXT,
                        value TEXT,
                        source TEXT,
                        confidence REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, key)
                    );

                    CREATE TABLE IF NOT EXISTS metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    );

                    -- Indexes for performance
                    CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
                    CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
                    CREATE INDEX IF NOT EXISTS idx_facts_user ON facts(user_id);
                """)
                
                # Initial metadata insertion
                cursor.execute("INSERT OR IGNORE INTO metadata (key, value) VALUES ('schema_version', '1.1')")
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Init DB failed: {e}")

    # ==========================
    # User Management
    # ==========================
    def get_or_create_user(self, platform: str, platform_user_id: str, display_name: str = "Unknown") -> str:
        rows = self._execute(
            "SELECT id FROM users WHERE platform = ? AND platform_user_id = ?",
            (platform, str(platform_user_id)), commit=False
        )
        if rows:
            return rows[0][0]
        
        user_id = uuid.uuid4().hex
        self._execute(
            "INSERT INTO users (id, platform, platform_user_id, display_name) VALUES (?, ?, ?, ?)",
            (user_id, platform, str(platform_user_id), display_name)
        )
        return user_id

    # ==========================
    # Session Management
    # ==========================
    def create_session(self, user_id: str, module: str, title: str = "New Session") -> str:
        session_id = uuid.uuid4().hex
        self._execute(
            "INSERT INTO sessions (id, user_id, module, title) VALUES (?, ?, ?, ?)",
            (session_id, user_id, module, title)
        )
        return session_id

    def get_last_session(self, user_id: str, module: str) -> Optional[str]:
        """Resume the most recently updated session for a specific module."""
        rows = self._execute(
            "SELECT id FROM sessions WHERE user_id = ? AND module = ? ORDER BY updated_at DESC LIMIT 1",
            (user_id, module), commit=False
        )
        return rows[0][0] if rows else None

    def set_session_title(self, session_id: str, title: str):
        self._execute(
            "UPDATE sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (title, session_id)
        )
        
    def save_session_summary(self, session_id: str, summary: str):
        self._execute(
            "UPDATE sessions SET summary = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (summary, session_id)
        )

    # ==========================
    # Message Flow
    # ==========================
    def append(self, session_id: str, role: str, content: str, 
               input_type: str = "text", token_estimate: int = 0,
               model: Optional[str] = None, temperature: Optional[float] = None, 
               latency_ms: Optional[int] = None):
        msg_id = uuid.uuid4().hex
        
        with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.execute("BEGIN TRANSACTION")
                    conn.execute(
                        """INSERT INTO messages 
                           (id, session_id, role, content, input_type, token_estimate, model, temperature, latency_ms) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (msg_id, session_id, role, content, input_type, token_estimate, model, temperature, latency_ms)
                    )
                    conn.execute(
                        "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (session_id,)
                    )
                    conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Failed to append message: {e}")
                raise DatabaseError("Message append failed")

    def history(self, session_id: str, limit: int = 12) -> List[Dict]:
        """Fetch the latest messages, ordered absolutely by rowid to prevent timestamp collisions."""
        rows = self._execute(
            """SELECT role, content, input_type, timestamp FROM messages 
               WHERE session_id = ? AND deleted = 0 
               ORDER BY rowid DESC LIMIT ?""",
            (session_id, limit), commit=False
        )
        # Reverse to return chronological order
        return [{"role": r[0], "content": r[1], "input_type": r[2], "timestamp": r[3]} for r in reversed(rows)]

    def get_session_context(self, session_id: str, limit: int = 12) -> Dict:
        """Fetch both the recent messages AND the session summary (if any)."""
        rows = self._execute("SELECT summary FROM sessions WHERE id = ?", (session_id,), commit=False)
        summary = rows[0][0] if rows else None
        return {
            "summary": summary,
            "messages": self.history(session_id, limit)
        }

    def rollback(self, session_id: str):
        """Soft delete the last message."""
        rows = self._execute(
            "SELECT id FROM messages WHERE session_id = ? AND deleted = 0 ORDER BY rowid DESC LIMIT 1",
            (session_id,), commit=False
        )
        if rows:
            self._execute("UPDATE messages SET deleted = 1 WHERE id = ?", (rows[0][0],))

    def clear_session(self, session_id: str):
        """Wipe the context by soft-deleting all messages in the session."""
        self._execute("UPDATE messages SET deleted = 1 WHERE session_id = ?", (session_id,))

    def export(self, session_id: str) -> str:
        session_info = self._execute("SELECT title, created_at FROM sessions WHERE id = ?", (session_id,), commit=False)
        if not session_info:
            return "Session not found."
            
        title, created_at = session_info[0]
        md_output = f"# 🌙 Session: {title}\n*Started at: {created_at}*\n\n---\n\n"
        
        messages = self._execute(
            "SELECT role, content, input_type FROM messages WHERE session_id = ? AND deleted = 0 ORDER BY rowid ASC",
            (session_id,), commit=False
        )
        for role, content, input_type in messages:
            badge = f" `[{input_type.upper()}]`" if input_type != "text" else ""
            md_output += f"### {role.capitalize()}{badge}\n{content}\n\n"
            
        return md_output

    def search_messages(self, user_id: str, keyword: str) -> List[Dict]:
        """Search across all active sessions for a user."""
        query = f"%{keyword}%"
        rows = self._execute(
            """SELECT s.title, m.role, m.content, m.timestamp 
               FROM messages m
               JOIN sessions s ON m.session_id = s.id
               WHERE s.user_id = ? AND m.content LIKE ? AND m.deleted = 0
               ORDER BY m.rowid DESC LIMIT 50""",
            (user_id, query), commit=False
        )
        return [{"session": r[0], "role": r[1], "content": r[2], "timestamp": r[3]} for r in rows]

    # ==========================
    # Persistent Facts
    # ==========================
    def save_fact(self, user_id: str, key: str, value: str, source: str = "user", confidence: float = 1.0):
        fact_id = uuid.uuid4().hex
        self._execute(
            """INSERT INTO facts (id, user_id, key, value, source, confidence, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
               ON CONFLICT(user_id, key) DO UPDATE SET 
               value=excluded.value, source=excluded.source, 
               confidence=excluded.confidence, updated_at=CURRENT_TIMESTAMP""",
            (fact_id, user_id, key, value, source, confidence)
        )

    def load_facts(self, user_id: str, min_confidence: float = 0.8) -> Dict[str, str]:
        rows = self._execute(
            "SELECT key, value FROM facts WHERE user_id = ? AND confidence >= ?",
            (user_id, min_confidence), commit=False
        )
        return {r[0]: r[1] for r in rows}

# Global MemoryStore Service
memory_store = MemoryStore()
