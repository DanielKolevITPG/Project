from database.db import execute_query, get_connection
from typing import Optional, List, Dict, Any
import re


class LeagueValidationError(Exception):
    """Custom exception for league validation errors."""

    pass


class LeagueNotFoundError(Exception):
    """Custom exception when league is not found."""

    pass


class ClubNotFoundError(Exception):
    """Custom exception when club is not found."""

    pass


def validate_season_format(season: str) -> bool:
    """Validate that season is in format YYYY/YYYY."""
    pattern = r"^\d{4}/\d{4}$"
    return bool(re.match(pattern, season))


def find_club_id(club_name: str) -> Optional[int]:
    """Find club ID by name. Returns None if not found."""
    club = execute_query(
        "SELECT id FROM clubs WHERE name = ?", (club_name,), fetchone=True
    )
    if club:
        return club["id"]
    return None


def find_club_name_by_id(club_id: int) -> Optional[str]:
    """Find club name by ID. Returns None if not found."""
    club = execute_query(
        "SELECT name FROM clubs WHERE id = ?", (club_id,), fetchone=True
    )
    return club["name"] if club else None


def find_league_id(name: str, season: str) -> Optional[int]:
    """Find league ID by name and season. Returns None if not found."""
    league = execute_query(
        "SELECT id FROM leagues WHERE name = ? AND season = ?",
        (name, season),
        fetchone=True,
    )
    if league:
        return league["id"]
    return None


def get_league_by_id(league_id: int) -> Optional[Dict[str, Any]]:
    """Get league by ID. Returns None if not found."""
    league = execute_query(
        "SELECT * FROM leagues WHERE id = ?", (league_id,), fetchone=True
    )
    return dict(league) if league else None


def create_league(name: str, season: str) -> str:
    """
    Create a new league.

    Args:
        name: League name
        season: Season in format YYYY/YYYY

    Returns:
        Success message with league ID

    Raises:
        LeagueValidationError: If validation fails
    """
    if not name or not name.strip():
        raise LeagueValidationError("Името на лигата е задължително.")

    if not season or not season.strip():
        raise LeagueValidationError("Сезонът е задължителен.")

    if not validate_season_format(season):
        raise LeagueValidationError(
            "Невалиден формат на сезона. Очаква се формат YYYY/YYYY (напр. 2025/2026)."
        )

    try:
        execute_query(
            "INSERT INTO leagues (name, season) VALUES (?, ?)",
            (name.strip(), season.strip()),
            commit=True,
        )

        # Get the created league ID
        league_id = execute_query(
            "SELECT id FROM leagues WHERE name = ? AND season = ?",
            (name.strip(), season.strip()),
            fetchone=True,
        )

        return (
            f"Лига '{name}' сезон {season} е създадена успешно (ID: {league_id['id']})."
        )
    except Exception as e:
        if "UNIQUE" in str(e).upper() or "unique" in str(e).lower():
            raise LeagueValidationError(
                f"Лига '{name}' сезон {season} вече съществува."
            )
        raise RuntimeError(f"Грешка при създаване на лига: {e}")


def add_team_to_league(league_name: str, season: str, club_name: str) -> str:
    """
    Add a club to a league.

    Args:
        league_name: League name
        season: Season
        club_name: Club name

    Returns:
        Success message

    Raises:
        LeagueNotFoundError: If league doesn't exist
        ClubNotFoundError: If club doesn't exist
        LeagueValidationError: If club already in league
    """
    league_id = find_league_id(league_name, season)
    if league_id is None:
        raise LeagueNotFoundError(f"Няма лига с име '{league_name}' сезон {season}.")

    club_id = find_club_id(club_name)
    if club_id is None:
        raise ClubNotFoundError(f"Клубът '{club_name}' не съществува.")

    # Check if club is already in league
    existing = execute_query(
        "SELECT 1 FROM league_teams WHERE league_id = ? AND club_id = ?",
        (league_id, club_id),
        fetchone=True,
    )
    if existing:
        raise LeagueValidationError(f"Клуб '{club_name}' вече е добавен в тази лига.")

    try:
        execute_query(
            "INSERT INTO league_teams (league_id, club_id) VALUES (?, ?)",
            (league_id, club_id),
            commit=True,
        )
        return f"Клуб '{club_name}' е добавен в лига '{league_name}' {season}."
    except Exception as e:
        raise RuntimeError(f"Грешка при добавяне на отбор: {e}")


def remove_team_from_league(league_name: str, season: str, club_name: str) -> str:
    """
    Remove a club from a league.
    If matches already generated, they will be deleted.

    Args:
        league_name: League name
        season: Season
        club_name: Club name

    Returns:
        Success message

    Raises:
        LeagueNotFoundError: If league doesn't exist
        ClubNotFoundError: If club doesn't exist
        LeagueValidationError: If club not in league
    """
    league_id = find_league_id(league_name, season)
    if league_id is None:
        raise LeagueNotFoundError(f"Няма лига с име '{league_name}' сезон {season}.")

    club_id = find_club_id(club_name)
    if club_id is None:
        raise ClubNotFoundError(f"Клубът '{club_name}' не съществува.")

    # Check if club is in league
    existing = execute_query(
        "SELECT 1 FROM league_teams WHERE league_id = ? AND club_id = ?",
        (league_id, club_id),
        fetchone=True,
    )
    if not existing:
        raise LeagueValidationError(f"Клуб '{club_name}' не е в тази лига.")

    # Check if matches exist and delete them
    matches_exist = execute_query(
        "SELECT 1 FROM matches WHERE league_id = ? LIMIT 1", (league_id,), fetchone=True
    )

    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Delete matches if any
        if matches_exist:
            cur.execute("DELETE FROM matches WHERE league_id = ?", (league_id,))

        # Remove club from league
        cur.execute(
            "DELETE FROM league_teams WHERE league_id = ? AND club_id = ?",
            (league_id, club_id),
        )

        conn.commit()

        msg = f"Клуб '{club_name}' е премахнат от лига '{league_name}' {season}."
        if matches_exist:
            msg += " Генерираните мачове са изтрити."
        return msg
    except Exception as e:
        if conn:
            conn.rollback()
        raise RuntimeError(f"Грешка при премахване на отбор: {e}")


def get_teams_in_league(league_name: str, season: str) -> str:
    """
    Get all teams in a league.

    Args:
        league_name: League name
        season: Season

    Returns:
        Formatted string of teams

    Raises:
        LeagueNotFoundError: If league doesn't exist
    """
    league_id = find_league_id(league_name, season)
    if league_id is None:
        raise LeagueNotFoundError(f"Няма лига с име '{league_name}' сезон {season}.")

    teams = execute_query(
        """
        SELECT c.id, c.name
        FROM clubs c
        JOIN league_teams lt ON c.id = lt.club_id
        WHERE lt.league_id = ?
        ORDER BY c.name
        """,
        (league_id,),
        fetchall=True,
    )

    if not teams:
        return f"Няма отбори в лига '{league_name}' {season}."

    lines = [f"Отбори в '{league_name}' {season}:"]
    for t in teams:
        lines.append(f"  {t['id']}: {t['name']}")

    return "\n".join(lines)


def get_team_ids_in_league(league_id: int) -> List[int]:
    """Get list of team IDs in a league."""
    teams = execute_query(
        "SELECT club_id FROM league_teams WHERE league_id = ?",
        (league_id,),
        fetchall=True,
    )
    return [t["club_id"] for t in teams]


def generate_round_robin_schedule(
    league_name: str, season: str, force: bool = False
) -> str:
    """
    Generate a round-robin schedule for a league.
    Each team plays every other team once (single round-robin).
    If odd number of teams, adds a BYE.

    Args:
        league_name: League name
        season: Season
        force: If True, regenerate even if matches exist

    Returns:
        Success message with schedule summary

    Raises:
        LeagueNotFoundError: If league doesn't exist
        LeagueValidationError: If not enough teams or matches already exist
    """
    league_id = find_league_id(league_name, season)
    if league_id is None:
        raise LeagueNotFoundError(f"Няма лига с име '{league_name}' сезон {season}.")

    # Get teams
    team_ids = get_team_ids_in_league(league_id)
    num_teams = len(team_ids)

    if num_teams < 4:
        raise LeagueValidationError(
            f"Недостатъчно отбори за програма (минимум 4). В момента има {num_teams}."
        )

    # Check if matches already exist
    existing_matches = execute_query(
        "SELECT COUNT(*) as count FROM matches WHERE league_id = ?",
        (league_id,),
        fetchone=True,
    )

    if existing_matches and existing_matches["count"] > 0 and not force:
        raise LeagueValidationError(
            f"Вече има генерирана програма ({existing_matches['count']} мача). "
            f"Използвайте 'прегенерирай' за да я изтриете и създадете нова."
        )

    # Generate round-robin schedule
    schedule = _create_round_robin(team_ids)

    # Insert matches into database
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Delete existing matches if force=True
        if force and existing_matches and existing_matches["count"] > 0:
            cur.execute("DELETE FROM matches WHERE league_id = ?", (league_id,))

        total_matches = 0
        for round_num, matches in schedule.items():
            for home_id, away_id in matches:
                cur.execute(
                    """
                    INSERT INTO matches (league_id, round_no, home_club_id, away_club_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (league_id, round_num, home_id, away_id),
                )
                total_matches += 1

        conn.commit()

        # Build summary
        num_rounds = len(schedule)
        lines = [
            f"Програмата за '{league_name}' {season} е генерирана успешно!",
            f"  Кръгове: {num_rounds}",
            f"  Общо мачове: {total_matches}",
            f"  Отбори: {num_teams}",
            "",
            "Примерен първи кръг:",
        ]

        if 1 in schedule:
            for home_id, away_id in schedule[1]:
                home_name = find_club_name_by_id(home_id)
                away_name = find_club_name_by_id(away_id)
                lines.append(f"  {home_name} vs {away_name}")

        return "\n".join(lines)

    except Exception as e:
        if conn:
            conn.rollback()
        raise RuntimeError(f"Грешка при генериране на програмата: {e}")


def _create_round_robin(team_ids: List[int]) -> Dict[int, List[tuple]]:
    """
    Create a single round-robin schedule.
    Uses circle method (Berger tables).

    Args:
        team_ids: List of team IDs

    Returns:
        Dictionary mapping round number to list of (home, away) tuples
    """
    # If odd number of teams, add a "BYE" (None)
    teams = list(team_ids)
    if len(teams) % 2 == 1:
        teams.append(None)

    n = len(teams)
    num_rounds = n - 1

    # Fixed position for first team, rotate others
    fixed = teams[0]
    rotating = teams[1:]

    schedule = {}

    for round_num in range(1, num_rounds + 1):
        matches = []

        # First team plays against last team in rotating list
        opponent = rotating[-1]
        if fixed is not None and opponent is not None:
            matches.append((fixed, opponent))

        # Remaining teams are paired: 1st with last, 2nd with 2nd last, etc.
        for i in range(len(rotating) // 2 - 1):
            team1 = rotating[i]
            team2 = rotating[len(rotating) - 2 - i]
            if team1 is not None and team2 is not None:
                matches.append((team1, team2))

        schedule[round_num] = matches

        # Rotate the list (last element goes to front)
        rotating = [rotating[-1]] + rotating[:-1]

    return schedule


def delete_league(name: str, season: str) -> str:
    """
    Delete a league and all its associated data (teams, matches).

    Args:
        name: League name
        season: Season

    Returns:
        Success message

    Raises:
        LeagueNotFoundError: If league doesn't exist
    """
    league_id = find_league_id(name, season)
    if league_id is None:
        raise LeagueNotFoundError(f"Няма лига с име '{name}' сезон {season}.")

    try:
        execute_query("DELETE FROM leagues WHERE id = ?", (league_id,), commit=True)
        return f"Лига '{name}' сезон {season} е изтрита."
    except Exception as e:
        raise RuntimeError(f"Грешка при изтриване на лига: {e}")


def get_league_schedule(league_name: str, season: str) -> str:
    """
    Get the schedule for a league.

    Args:
        league_name: League name
        season: Season

    Returns:
        Formatted string of schedule

    Raises:
        LeagueNotFoundError: If league doesn't exist
    """
    league_id = find_league_id(league_name, season)
    if league_id is None:
        raise LeagueNotFoundError(f"Няма лига с име '{league_name}' сезон {season}.")

    matches = execute_query(
        """
        SELECT m.round_no, m.home_club_id, m.away_club_id,
               c_home.name as home_name, c_away.name as away_name,
               m.home_goals, m.away_goals
        FROM matches m
        JOIN clubs c_home ON m.home_club_id = c_home.id
        JOIN clubs c_away ON m.away_club_id = c_away.id
        WHERE m.league_id = ?
        ORDER BY m.round_no, m.id
        """,
        (league_id,),
        fetchall=True,
    )

    if not matches:
        return f"Няма генерирана програма за лига '{league_name}' {season}."

    lines = [f"Програма за '{league_name}' {season}:", ""]
    current_round = 0

    for m in matches:
        if m["round_no"] != current_round:
            current_round = m["round_no"]
            lines.append(f"Кръг {current_round}:")

        score = ""
        if m["home_goals"] is not None and m["away_goals"] is not None:
            score = f" {m['home_goals']}-{m['away_goals']}"

        lines.append(f"  {m['home_name']} vs {m['away_name']}{score}")

    return "\n".join(lines)
