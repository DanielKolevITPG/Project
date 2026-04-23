from src.database import db as _db
import sqlite3


# Expose connection used by the application (and tests can override it)
_conn = None


def get_connection(db_path=None):
    global _conn
    if _conn is not None:
        return _conn
    return _db.get_connection(db_path)


def execute_query(sql, params=(), commit=False, fetchone=False, fetchall=False):
    # Use overridden connection if present
    conn = get_connection()
    try:
        # Ensure sqlite3.Row results for dict-like access
        try:
            conn.row_factory = sqlite3.Row
        except Exception:
            pass
        cur = conn.cursor()
        cur.execute(sql, params)
        if commit:
            conn.commit()
        if fetchone:
            return cur.fetchone()
        if fetchall:
            return cur.fetchall() or []
        return cur.rowcount
    except Exception:
        raise


__all__ = ["get_connection", "execute_query", "_conn"]
