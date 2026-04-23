from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from src.db import execute_query, get_connection


def get_league_id_by_name_season(name: str, season: str) -> Optional[int]:
    row = execute_query(
        "SELECT id FROM leagues WHERE name = ? AND season = ?",
        (name, season),
        fetchone=True,
    )
    return int(row["id"]) if row else None


def get_match_by_id(match_id: int) -> Optional[Dict[str, Any]]:
    row = execute_query(
        """
        SELECT m.*, c_home.name AS home_name, c_away.name AS away_name
        FROM matches m
        JOIN clubs c_home ON c_home.id = m.home_club_id
        JOIN clubs c_away ON c_away.id = m.away_club_id
        WHERE m.id = ?
        """,
        (match_id,),
        fetchone=True,
    )
    return dict(row) if row else None


def list_round_matches(league_id: int, round_no: int) -> List[Dict[str, Any]]:
    rows = execute_query(
        """
        SELECT m.id, m.round_no, m.status, m.home_goals, m.away_goals,
               c_home.name AS home_name, c_away.name AS away_name
        FROM matches m
        JOIN clubs c_home ON c_home.id = m.home_club_id
        JOIN clubs c_away ON c_away.id = m.away_club_id
        WHERE m.league_id = ? AND m.round_no = ?
        ORDER BY m.id
        """,
        (league_id, round_no),
        fetchall=True,
    )
    return [dict(r) for r in (rows or [])]


def find_matches_by_teams_in_league(
    league_id: int, home_club_id: int, away_club_id: int
) -> List[Dict[str, Any]]:
    rows = execute_query(
        """
        SELECT m.id, m.round_no, m.status, m.home_goals, m.away_goals,
               c_home.name AS home_name, c_away.name AS away_name
        FROM matches m
        JOIN clubs c_home ON c_home.id = m.home_club_id
        JOIN clubs c_away ON c_away.id = m.away_club_id
        WHERE m.league_id = ? AND m.home_club_id = ? AND m.away_club_id = ?
        ORDER BY m.round_no, m.id
        """,
        (league_id, home_club_id, away_club_id),
        fetchall=True,
    )
    return [dict(r) for r in (rows or [])]


def find_club_id_by_name(club_name: str) -> Optional[int]:
    row = execute_query(
        "SELECT id FROM clubs WHERE name = ?",
        (club_name,),
        fetchone=True,
    )
    return int(row["id"]) if row else None


def find_player_by_name_and_club(
    player_name: str, club_id: int
) -> Optional[Dict[str, Any]]:
    row = execute_query(
        """
        SELECT id, full_name, club_id
        FROM players
        WHERE full_name = ? AND club_id = ?
        """,
        (player_name, club_id),
        fetchone=True,
    )
    return dict(row) if row else None


def get_match_participant_club_ids(match_id: int) -> Optional[Tuple[int, int]]:
    row = execute_query(
        "SELECT home_club_id, away_club_id FROM matches WHERE id = ?",
        (match_id,),
        fetchone=True,
    )
    if not row:
        return None
    return (int(row["home_club_id"]), int(row["away_club_id"]))


def update_match_result(match_id: int, home_goals: int, away_goals: int) -> int:
    return int(
        execute_query(
            """
            UPDATE matches
            SET home_goals = ?, away_goals = ?, status = 'played'
            WHERE id = ?
            """,
            (home_goals, away_goals, match_id),
            commit=True,
        )
    )


def insert_goal(match_id: int, player_id: int, club_id: int, minute: int) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO goals (match_id, player_id, club_id, minute)
        VALUES (?, ?, ?, ?)
        """,
        (match_id, player_id, club_id, minute),
    )
    last = cur.lastrowid
    return int(last) if last is not None else 0


def insert_card(
    match_id: int, player_id: int, club_id: int, card_type: str, minute: int
) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO cards (match_id, player_id, club_id, card_type, minute)
        VALUES (?, ?, ?, ?, ?)
        """,
        (match_id, player_id, club_id, card_type, minute),
    )
    last = cur.lastrowid
    return int(last) if last is not None else 0


def count_red_cards_for_player(match_id: int, player_id: int) -> int:
    row = execute_query(
        """
        SELECT COUNT(*) AS cnt
        FROM cards
        WHERE match_id = ? AND player_id = ? AND card_type = 'R'
        """,
        (match_id, player_id),
        fetchone=True,
    )
    return int(row["cnt"]) if row else 0


def count_yellow_cards_for_player(match_id: int, player_id: int) -> int:
    row = execute_query(
        """
        SELECT COUNT(*) AS cnt
        FROM cards
        WHERE match_id = ? AND player_id = ? AND card_type = 'Y'
        """,
        (match_id, player_id),
        fetchone=True,
    )
    return int(row["cnt"]) if row else 0


def list_match_events(match_id: int) -> List[Dict[str, Any]]:
    rows = execute_query(
        """
        SELECT
            g.minute AS minute,
            'GOAL' AS event_type,
            p.full_name AS player_name,
            c.name AS club_name,
            NULL AS card_type
        FROM goals g
        JOIN players p ON p.id = g.player_id
        JOIN clubs c ON c.id = g.club_id
        WHERE g.match_id = ?

        UNION ALL

        SELECT
            ca.minute AS minute,
            'CARD' AS event_type,
            p.full_name AS player_name,
            c.name AS club_name,
            ca.card_type AS card_type
        FROM cards ca
        JOIN players p ON p.id = ca.player_id
        JOIN clubs c ON c.id = ca.club_id
        WHERE ca.match_id = ?

        ORDER BY minute ASC, event_type ASC
        """,
        (match_id, match_id),
        fetchall=True,
    )
    return [dict(r) for r in (rows or [])]


def commit(conn) -> None:
    conn.commit()


def rollback(conn) -> None:
    conn.rollback()
