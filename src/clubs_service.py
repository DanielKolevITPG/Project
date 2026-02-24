import typing
from typing import List, Dict, Union

# ...existing code...
import db
import sqlite3

def add_club(name: str) -> Dict[str, Union[bool, str, int]]:
    """
    Add a club after validation:
    - trim whitespace
    - non-empty
    - no duplicate names
    Returns dict with success and message (and id on success).
    """
    if name is None:
        return {"success": False, "message": "Club name is required."}
    name_clean = name.strip()
    if not name_clean:
        return {"success": False, "message": "Club name must not be empty."}

    # Check duplicate
    try:
        existing = db.execute_query(
            "SELECT id FROM clubs WHERE name = ?",
            (name_clean,), fetchone=True
        )
        if existing:
            return {"success": False, "message": "Club with this name already exists."}

        # Insert
        db.execute_query(
            "INSERT INTO clubs (name) VALUES (?)",
            (name_clean,), commit=True
        )
        # Get last inserted id
        conn = db.get_connection()
        last_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return {"success": True, "message": "Club added.", "id": int(last_id)}
    except sqlite3.IntegrityError:
        return {"success": False, "message": "Club with this name already exists (integrity)."}
    except Exception as e:
        return {"success": False, "message": f"Error adding club: {e}"}

def get_all_clubs() -> List[Dict[str, typing.Any]]:
    """
    Return list of clubs as dicts: [{'id': int, 'name': str}, ...]
    """
    try:
        rows = db.execute_query("SELECT id, name FROM clubs ORDER BY id ASC", fetchall=True)
        if not rows:
            return []
        return [{"id": int(r["id"]), "name": r["name"]} for r in rows]
    except Exception:
        return []

def delete_club(name_or_id: Union[str, int]) -> Dict[str, Union[bool, str]]:
    """
    Delete by id (if integer-like) or by exact name.
    """
    try:
        if isinstance(name_or_id, int) or (isinstance(name_or_id, str) and name_or_id.strip().isdigit()):
            club_id = int(str(name_or_id).strip())
            cur = db.execute_query("DELETE FROM clubs WHERE id = ?", (club_id,), commit=True)
            # cur is rowcount
            if cur and cur > 0:
                return {"success": True, "message": "Club deleted by id."}
            return {"success": False, "message": "Club with given id not found."}
        else:
            name_clean = str(name_or_id).strip()
            if not name_clean:
                return {"success": False, "message": "Club name must not be empty."}
            cur = db.execute_query("DELETE FROM clubs WHERE name = ?", (name_clean,), commit=True)
            if cur and cur > 0:
                return {"success": True, "message": "Club deleted by name."}
            return {"success": False, "message": "Club with given name not found."}
    except Exception as e:
        return {"success": False, "message": f"Error deleting club: {e}"}

def update_club(club_id: int, new_name: str) -> Dict[str, Union[bool, str]]:
    """
    Optional: Update club name with validation.
    """
    try:
        if not new_name or not new_name.strip():
            return {"success": False, "message": "New name must not be empty."}
        new_clean = new_name.strip()
        # Check duplicate
        existing = db.execute_query("SELECT id FROM clubs WHERE name = ?", (new_clean,), fetchone=True)
        if existing and existing["id"] != club_id:
            return {"success": False, "message": "Another club with this name exists."}
        res = db.execute_query("UPDATE clubs SET name = ? WHERE id = ?", (new_clean, club_id), commit=True)
        if res and res > 0:
            return {"success": True, "message": "Club updated."}
        return {"success": False, "message": "Club not found."}
    except sqlite3.IntegrityError:
        return {"success": False, "message": "Club with this name already exists."}
    except Exception as e:
        return {"success": False, "message": f"Error updating club: {e}"}