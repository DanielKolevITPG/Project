from src.db import execute_query


def add_club(name):
    name = (name or "").strip()
    if not name:
        return {"message": "Името на клуба е задължително."}

    try:
        execute_query("INSERT INTO clubs(name) VALUES (?)", (name,), commit=True)
        return {"message": f"Клуб '{name}' е добавен."}
    except Exception:
        return {"message": "Клубът вече съществува."}


def get_all_clubs():
    rows = execute_query("SELECT id,name FROM clubs", fetchall=True)
    return [dict(r) for r in (rows or [])]


def delete_club(name):
    name = (name or "").strip()
    if not name:
        return {"message": "Името на клуба е задължително."}

    affected = execute_query("DELETE FROM clubs WHERE name=?", (name,), commit=True)
    if not affected:
        return {"message": f"Няма клуб с име '{name}'."}
    return {"message": f"Клуб '{name}' е изтрит."}
