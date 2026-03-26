from database.db import execute_query
from datetime import datetime
from typing import Optional, List, Dict, Any

VALID_POSITIONS = ['GK', 'DF', 'MF', 'FW']
VALID_STATUS = ['active', 'injured', 'retired']


class PlayerValidationError(Exception):
    """Custom exception for player validation errors."""
    pass


class PlayerNotFoundError(Exception):
    """Custom exception when player is not found."""
    pass


class ClubNotFoundError(Exception):
    """Custom exception when club is not found."""
    pass


def validate_position(position: str) -> bool:
    """Validate that position is one of the allowed values."""
    return position in VALID_POSITIONS


def validate_number(number: int) -> bool:
    """Validate that number is between 1 and 99."""
    return isinstance(number, int) and 1 <= number <= 99


def validate_birthdate(date_text: str) -> bool:
    """Validate that birth_date is a valid date in the past."""
    try:
        birth_date = datetime.strptime(date_text, "%Y-%m-%d")
        return birth_date < datetime.now()
    except (ValueError, TypeError):
        return False


def validate_status(status: str) -> bool:
    """Validate that status is one of the allowed values."""
    return status in VALID_STATUS


def find_club_id(club_name: str) -> Optional[int]:
    """Find club ID by name. Returns None if not found."""
    club = execute_query(
        "SELECT id FROM clubs WHERE name = ?",
        (club_name,),
        fetchone=True
    )
    if club:
        return club['id']
    return None


def get_player_by_name(full_name: str) -> Optional[Dict[str, Any]]:
    """Find player by full name. Returns None if not found."""
    player = execute_query(
        "SELECT * FROM players WHERE full_name = ?",
        (full_name,),
        fetchone=True
    )
    return dict(player) if player else None


def get_player_by_id(player_id: int) -> Optional[Dict[str, Any]]:
    """Find player by ID. Returns None if not found."""
    player = execute_query(
        "SELECT * FROM players WHERE id = ?",
        (player_id,),
        fetchone=True
    )
    return dict(player) if player else None


def check_duplicate_number_in_club(club_id: int, number: int, exclude_player_id: Optional[int] = None) -> bool:
    """Check if a jersey number already exists in the club (excluding current player for updates)."""
    if exclude_player_id:
        query = "SELECT id FROM players WHERE club_id = ? AND number = ? AND id != ?"
        params = (club_id, number, exclude_player_id)
    else:
        query = "SELECT id FROM players WHERE club_id = ? AND number = ?"
        params = (club_id, number)
    result = execute_query(query, params, fetchone=True)
    return result is not None


def add_player(
    full_name: str,
    birth_date: str,
    nationality: str,
    position: str,
    number: int,
    club_name: str
) -> str:
    """
    Add a new player to the database.

    Args:
        full_name: Player's full name
        birth_date: Birth date in YYYY-MM-DD format
        nationality: Player's nationality
        position: One of 'GK', 'DF', 'MF', 'FW'
        number: Jersey number (1-99)
        club_name: Name of the club

    Returns:
        Success message

    Raises:
        PlayerValidationError: If validation fails
        ClubNotFoundError: If club doesn't exist
    """
    # Validate required fields
    if not full_name or not isinstance(full_name, str) or not full_name.strip():
        raise PlayerValidationError("Името на играча е задължително.")

    if not birth_date or not validate_birthdate(birth_date):
        raise PlayerValidationError("Невалидна дата на раждане. Използвайте формат YYYY-MM-DD и дата в миналото.")

    if not nationality or not isinstance(nationality, str) or not nationality.strip():
        raise PlayerValidationError("Националността е задължителна.")

    if not validate_position(position):
        raise PlayerValidationError(f"Невалидна позиция. Допустими стойности: {', '.join(VALID_POSITIONS)}")

    if not validate_number(number):
        raise PlayerValidationError("Номерът трябва да е между 1 и 99.")

    # Find club
    club_id = find_club_id(club_name)
    if club_id is None:
        raise ClubNotFoundError(f"Клубът '{club_name}' не съществува.")

    # Check for duplicate jersey number in club
    if check_duplicate_number_in_club(club_id, number):
        raise PlayerValidationError(f"Номер {number} вече се използва в клуба '{club_name}'.")

    # Insert player
    try:
        execute_query(
            """
            INSERT INTO players (full_name, birth_date, nationality, position, number, club_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (full_name.strip(), birth_date, nationality.strip(), position, number, club_id, 'active'),
            commit=True
        )
        return f"Играч {full_name} е добавен успешно."
    except Exception as e:
        raise RuntimeError(f"Грешка при добавяне на играч: {e}")


def get_players(
    club_id: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = 0
) -> List[Dict[str, Any]]:
    """
    Retrieve players with optional filtering and pagination.

    Args:
        club_id: Filter by club ID (optional)
        limit: Maximum number of players to return (optional)
        offset: Number of players to skip (default 0)

    Returns:
        List of player dictionaries
    """
    query = "SELECT * FROM players"
    params = []

    if club_id is not None:
        query += " WHERE club_id = ?"
        params.append(club_id)

    query += " ORDER BY id"
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
        if offset:
            query += " OFFSET ?"
            params.append(offset)

    players = execute_query(query, tuple(params), fetchall=True)
    return [dict(p) for p in players]


def get_players_by_club_name(club_name: str) -> List[Dict[str, Any]]:
    """
    Retrieve all players for a specific club by name.

    Args:
        club_name: Name of the club

    Returns:
        List of player dictionaries

    Raises:
        ClubNotFoundError: If club doesn't exist
    """
    club_id = find_club_id(club_name)
    if club_id is None:
        raise ClubNotFoundError(f"Клубът '{club_name}' не съществува.")
    return get_players(club_id=club_id)


def update_player(
    player_id: int,
    position: Optional[str] = None,
    number: Optional[int] = None,
    status: Optional[str] = None
) -> str:
    """
    Update player's position, number, or status.

    Args:
        player_id: ID of the player to update
        position: New position (optional)
        number: New jersey number (optional)
        status: New status (optional)

    Returns:
        Success message

    Raises:
        PlayerNotFoundError: If player doesn't exist
        PlayerValidationError: If validation fails
    """
    # Get current player data
    player = get_player_by_id(player_id)
    if not player:
        raise PlayerNotFoundError(f"Играч с ID {player_id} не съществува.")

    updates = []
    params = []

    if position is not None:
        if not validate_position(position):
            raise PlayerValidationError(f"Невалидна позиция. Допустими стойности: {', '.join(VALID_POSITIONS)}")
        updates.append("position = ?")
        params.append(position)

    if number is not None:
        if not validate_number(number):
            raise PlayerValidationError("Номерът трябва да е между 1 и 99.")
        # Check for duplicate number in club
        if check_duplicate_number_in_club(player['club_id'], number, exclude_player_id=player_id):
            raise PlayerValidationError(f"Номер {number} вече се използва в този клуб.")
        updates.append("number = ?")
        params.append(number)

    if status is not None:
        if not validate_status(status):
            raise PlayerValidationError(f"Невалиден статус. Допустими стойности: {', '.join(VALID_STATUS)}")
        updates.append("status = ?")
        params.append(status)

    if not updates:
        return "Няма промени за прилагане."

    # Build and execute update query
    query = f"UPDATE players SET {', '.join(updates)} WHERE id = ?"
    params.append(player_id)

    try:
        execute_query(query, tuple(params), commit=True)
        return f"Играч с ID {player_id} е актуализиран успешно."
    except Exception as e:
        raise RuntimeError(f"Грешка при актуализация на играч: {e}")


def update_player_number(name: str, number: int) -> str:
    """
    Update player's jersey number by name (legacy function for chatbot compatibility).

    Args:
        name: Player's full name
        number: New jersey number

    Returns:
        Success message

    Raises:
        PlayerNotFoundError: If player doesn't exist
        PlayerValidationError: If validation fails
    """
    player = get_player_by_name(name)
    if not player:
        raise PlayerNotFoundError(f"Играч '{name}' не съществува.")

    return update_player(player['id'], number=number)


def update_player_status(name: str, status: str) -> str:
    """
    Update player's status by name.

    Args:
        name: Player's full name
        status: New status

    Returns:
        Success message

    Raises:
        PlayerNotFoundError: If player doesn't exist
        PlayerValidationError: If validation fails
    """
    player = get_player_by_name(name)
    if not player:
        raise PlayerNotFoundError(f"Играч '{name}' не съществува.")

    return update_player(player['id'], status=status)


def delete_player(player_id: int) -> str:
    """
    Delete a player by ID (hard delete).

    Args:
        player_id: ID of the player to delete

    Returns:
        Success message

    Raises:
        PlayerNotFoundError: If player doesn't exist
    """
    player = get_player_by_id(player_id)
    if not player:
        raise PlayerNotFoundError(f"Играч с ID {player_id} не съществува.")

    try:
        execute_query(
            "DELETE FROM players WHERE id = ?",
            (player_id,),
            commit=True
        )
        return f"Играч с ID {player_id} е изтрит."
    except Exception as e:
        raise RuntimeError(f"Грешка при изтриване на играч: {e}")


def delete_player_by_name(name: str) -> str:
    """
    Delete a player by name (legacy function for chatbot compatibility).

    Args:
        name: Player's full name

    Returns:
        Success message

    Raises:
        PlayerNotFoundError: If player doesn't exist
    """
    player = get_player_by_name(name)
    if not player:
        raise PlayerNotFoundError(f"Играч '{name}' не съществува.")

    return delete_player(player['id'])


def format_player_list(players: List[Dict[str, Any]]) -> str:
    """
    Format a list of players for display.

    Args:
        players: List of player dictionaries

    Returns:
        Formatted string for display
    """
    if not players:
        return "Няма намерени играчи."

    lines = []
    for p in players:
        lines.append(
            f"{p['full_name']} | {p['position']} | #{p['number']} | {p['nationality']} | {p['status']}"
        )
    return "\n".join(lines)
