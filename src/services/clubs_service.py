from database.db import execute_query


def add_club(name):

    try:
        execute_query(
            "INSERT INTO clubs(name) VALUES (?)",
            (name,),
            commit=True
        )
        return {"message": f"Клуб '{name}' е добавен."}

    except Exception:
        return {"message": "Клубът вече съществува."}


def get_all_clubs():

    rows = execute_query(
        "SELECT id,name FROM clubs",
        fetchall=True
    )

    return rows


def delete_club(name):

    execute_query(
        "DELETE FROM clubs WHERE name=?",
        (name,),
        commit=True
    )

    return {"message": f"Клуб '{name}' е изтрит."}


