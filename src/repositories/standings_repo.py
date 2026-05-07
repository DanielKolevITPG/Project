from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.db import execute_query


def get_league_id_by_name_season(name: str, season: str) -> Optional[int]:
    row = execute_query(
        "SELECT id FROM leagues WHERE name = ? AND season = ?",
        (name, season),
        fetchone=True,
    )
    return int(row["id"]) if row else None


def get_teams_in_league(league_id: int) -> List[Dict[str, Any]]:
    rows = execute_query(
        """
        SELECT c.id, c.name
        FROM league_teams lt
        JOIN clubs c ON c.id = lt.club_id
        WHERE lt.league_id = ?
        ORDER BY c.name
        """,
        (league_id,),
        fetchall=True,
    )
    return [dict(r) for r in (rows or [])]


def get_played_matches_for_league(league_id: int) -> List[Dict[str, Any]]:
    rows = execute_query(
        """
        SELECT
            m.home_club_id,
            m.away_club_id,
            m.home_goals,
            m.away_goals,
            m.status
        FROM matches m
        WHERE m.league_id = ? AND m.status = 'played' AND m.home_goals IS NOT NULL AND m.away_goals IS NOT NULL
        """,
        (league_id,),
        fetchall=True,
    )
    return [dict(r) for r in (rows or [])]


def get_head_to_head_matches(
    league_id: int, club_ids: List[int]
) -> List[Dict[str, Any]]:
    placeholders = ",".join("?" * len(club_ids))
    rows = execute_query(
        f"""
        SELECT
            m.home_club_id,
            m.away_club_id,
            m.home_goals,
            m.away_goals
        FROM matches m
        WHERE m.league_id = ?
          AND m.status = 'played'
          AND m.home_goals IS NOT NULL
          AND m.away_goals IS NOT NULL
          AND m.home_club_id IN ({placeholders})
          AND m.away_club_id IN ({placeholders})
        """,
        (league_id, *club_ids, *club_ids),
        fetchall=True,
    )
    return [dict(r) for r in (rows or [])]