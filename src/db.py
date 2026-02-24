import os
import sqlite3
import threading
from typing import Any, List, Optional, Tuple

# ...existing code...
_lock = threading.Lock()
_conn: Optional[sqlite3.Connection] = None

def _default_db_path() -> str:
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base, "data.db")

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Return a singleton sqlite3 connection. Thread-safe lazy init.
    """
    global _conn
    if db_path is None:
        db_path = _default_db_path()

    if _conn is None:
        with _lock:
            if _conn is None:
                try:
                    conn = sqlite3.connect(db_path, check_same_thread=False)
                    conn.row_factory = sqlite3.Row
                    _conn = conn
                except Exception as e:
                    raise RuntimeError(f"Failed to open database '{db_path}': {e}")
    return _conn

def execute_query(sql: str, params: Tuple = (), commit: bool = False,
                  fetchone: bool = False, fetchall: bool = False) -> Any:
    """
    Execute a query with proper error handling.
    Use fetchone or fetchall to return results.
    If commit=True, the transaction will be committed.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        if commit:
            conn.commit()
        if fetchone:
            return cur.fetchone()
        if fetchall:
            return cur.fetchall()
        return cur.rowcount
    except sqlite3.IntegrityError as e:
        # Propagate integrity errors (e.g., UNIQUE violation) with clear message
        raise
    except Exception as e:
        raise RuntimeError(f"Database query failed: {e}")