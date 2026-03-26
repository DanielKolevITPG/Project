from database.db import execute_query
from datetime import datetime
from typing import Optional, List, Dict, Any


class TransferValidationError(Exception):
    """Custom exception for transfer validation errors."""
    pass


class TransferNotFoundError(Exception):
    """Custom exception when transfer is not found."""
    pass


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


def find_club_name_by_id(club_id: int) -> Optional[str]:
    """Find club name by ID. Returns None if not found."""
    club = execute_query(
        "SELECT name FROM clubs WHERE id = ?",
        (club_id,),
        fetchone=True
    )
    return club['name'] if club else None


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


def validate_transfer_date(date_text: str) -> bool:
    """Validate that transfer_date is a valid date."""
    try:
        date = datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def validate_fee(fee: Optional[int]) -> bool:
    """Validate that fee is non-negative if provided."""
    if fee is None:
        return True
    return isinstance(fee, int) and fee >= 0


def transfer_player(
    player_name: str,
    from_club: str,
    to_club: str,
    date: str,
    fee: Optional[int] = None,
    note: Optional[str] = None
) -> str:
    """
    Transfer a player from one club to another.

    Args:
        player_name: Player's full name
        from_club: Name of the club the player is transferring from
        to_club: Name of the club the player is transferring to
        date: Transfer date in YYYY-MM-DD format
        fee: Transfer fee (optional)
        note: Additional note (optional)

    Returns:
        Success message with transfer details

    Raises:
        TransferValidationError: If validation fails
    """
    # Validate date
    if not validate_transfer_date(date):
        raise TransferValidationError("Невалидна дата. Използвайте формат YYYY-MM-DD.")

    # Validate fee
    if not validate_fee(fee):
        raise TransferValidationError("Сумата трябва да е положително число.")

    # Find player
    player = get_player_by_name(player_name)
    if not player:
        raise TransferValidationError(f"Играч '{player_name}' не съществува.")

    # Find clubs
    from_club_id = find_club_id(from_club)
    to_club_id = find_club_id(to_club)

    if to_club_id is None:
        raise TransferValidationError(f"Клубът '{to_club}' не съществува.")

    # Handle "free" transfer (player has no club)
    player_current_club_id = player.get('club_id')

    if player_current_club_id is None:
        # Player has no club - allow transfer only if from_club is "none/free"
        if from_club.lower() not in ['няма', 'свободен', 'free', 'none', '']:
            raise TransferValidationError(f"Играчът '{player_name}' няма клуб. За да бъде трансфериран, 'отбор от' трябва да е 'няма' или 'свободен'.")
        from_club_id = None
    else:
        # Player has a club - validate from_club matches
        if from_club_id is None:
            raise TransferValidationError(f"Клубът '{from_club}' не съществува.")

        if player_current_club_id != from_club_id:
            from_club_name = find_club_name_by_id(player_current_club_id)
            raise TransferValidationError(
                f"Играч '{player_name}' не принадлежи на клуб '{from_club}'. "
                f"Текущ клуб: {from_club_name}."
            )

    # Validate from != to (handled by DB constraint, but check explicitly)
    if from_club_id is not None and from_club_id == to_club_id:
        raise TransferValidationError("Отборът 'от' и 'към' не могат да бъдат еднакви.")

    # Atomic transfer: insert transfer record AND update player club_id
    conn = None
    try:
        from database.db import get_connection
        conn = get_connection()
        cur = conn.cursor()

        # Insert transfer record
        cur.execute(
            """
            INSERT INTO transfers (player_id, from_club_id, to_club_id, transfer_date, fee, note)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (player['id'], from_club_id, to_club_id, date, fee, note)
        )

        # Update player's club_id
        cur.execute(
            "UPDATE players SET club_id = ? WHERE id = ?",
            (to_club_id, player['id'])
        )

        # Commit both operations atomically
        conn.commit()

        from_club_display = from_club if from_club_id else "няма"
        to_club_display = to_club

        result = f"Успешен трансфер: {player_name} от {from_club_display} в {to_club_display} на {date}"
        if fee:
            result += f" със сума {fee}"
        if note:
            result += f". Забележка: {note}"

        return result

    except Exception as e:
        if conn:
            conn.rollback()
        raise RuntimeError(f"Грешка при трансфер: {e}")


def list_transfers_by_player(player_name: str) -> str:
    """
    List all transfers for a specific player.

    Args:
        player_name: Player's full name

    Returns:
        Formatted string of transfers

    Raises:
        TransferValidationError: If player doesn't exist
    """
    player = get_player_by_name(player_name)
    if not player:
        raise TransferValidationError(f"Играч '{player_name}' не съществува.")

    transfers = execute_query(
        """
        SELECT t.*, 
               c_from.name as from_club_name, 
               c_to.name as to_club_name
        FROM transfers t
        LEFT JOIN clubs c_from ON t.from_club_id = c_from.id
        LEFT JOIN clubs c_to ON t.to_club_id = c_to.id
        WHERE t.player_id = ?
        ORDER BY t.transfer_date DESC
        """,
        (player['id'],),
        fetchall=True
    )

    if not transfers:
        return f"Няма трансфери за играч '{player_name}'."

    lines = [f"Трансфери на {player_name}:"]
    for t in transfers:
        from_name = t['from_club_name'] if t['from_club_name'] else "няма"
        to_name = t['to_club_name']
        fee_str = f" | Сума: {t['fee']}" if t['fee'] else ""
        lines.append(f"  {t['transfer_date']}: {from_name} → {to_name}{fee_str}")

    return "\n".join(lines)


def list_transfers_by_club(club_name: str) -> str:
    """
    List all transfers for a specific club (as source or destination).

    Args:
        club_name: Club's name

    Returns:
        Formatted string of transfers

    Raises:
        TransferValidationError: If club doesn't exist
    """
    club_id = find_club_id(club_name)
    if club_id is None:
        raise TransferValidationError(f"Клубът '{club_name}' не съществува.")

    transfers = execute_query(
        """
        SELECT t.*, 
               p.full_name as player_name,
               c_from.name as from_club_name, 
               c_to.name as to_club_name
        FROM transfers t
        JOIN players p ON t.player_id = p.id
        LEFT JOIN clubs c_from ON t.from_club_id = c_from.id
        LEFT JOIN clubs c_to ON t.to_club_id = c_to.id
        WHERE t.from_club_id = ? OR t.to_club_id = ?
        ORDER BY t.transfer_date DESC
        """,
        (club_id, club_id),
        fetchall=True
    )

    if not transfers:
        return f"Няма трансфери за клуб '{club_name}'."

    lines = [f"Трансфери на {club_name}:"]
    for t in transfers:
        from_name = t['from_club_name'] if t['from_club_name'] else "няма"
        to_name = t['to_club_name']
        direction = "→" if t['from_club_id'] == club_id else "←"
        fee_str = f" | Сума: {t['fee']}" if t['fee'] else ""
        lines.append(f"  {t['transfer_date']}: {t['player_name']} {direction} {to_name}{fee_str}")

    return "\n".join(lines)
