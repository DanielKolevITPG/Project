from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional, Sequence, Tuple

from src.db import execute_query


MIN_MATCHES_REQUIRED = 5


@dataclass
class TeamState:
    matches: int = 0
    points: int = 0
    goals_for: int = 0
    goals_against: int = 0
    form_points: Deque[int] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.form_points is None:
            self.form_points = deque(maxlen=5)


def get_team_by_name(team_name: str) -> Optional[Dict[str, object]]:
    name = team_name.strip()
    row = execute_query(
        "SELECT id, name FROM clubs WHERE LOWER(name) = LOWER(?)",
        (name,),
        fetchone=True,
    )
    if row:
        return dict(row)

    rows = execute_query(
        "SELECT id, name FROM clubs WHERE LOWER(name) LIKE LOWER(?) ORDER BY LENGTH(name) ASC",
        (f"{name}%",),
        fetchall=True,
    )
    if rows and len(rows) == 1:
        return dict(rows[0])

    rows = execute_query(
        "SELECT id, name FROM clubs WHERE LOWER(name) LIKE LOWER(?) ORDER BY LENGTH(name) ASC",
        (f"%{name}%",),
        fetchall=True,
    )
    if rows and len(rows) == 1:
        return dict(rows[0])

    return None


def get_common_league_id(home_team_id: int, away_team_id: int) -> Optional[int]:
    rows = execute_query(
        """
        SELECT lt1.league_id
        FROM league_teams lt1
        JOIN league_teams lt2 ON lt1.league_id = lt2.league_id
        WHERE lt1.club_id = ? AND lt2.club_id = ?
        """,
        (home_team_id, away_team_id),
        fetchall=True,
    )
    if not rows:
        return None

    league_ids = [int(r["league_id"]) for r in rows]
    # Prefer the league with most played matches (best training signal)
    best_league_id = None
    best_count = -1
    for league_id in league_ids:
        count_row = execute_query(
            """
            SELECT COUNT(*) AS cnt
            FROM matches
            WHERE league_id = ?
              AND status = 'played'
              AND home_goals IS NOT NULL
              AND away_goals IS NOT NULL
            """,
            (league_id,),
            fetchone=True,
        )
        cnt = int(count_row["cnt"]) if count_row else 0
        if cnt > best_count:
            best_count = cnt
            best_league_id = league_id
    return best_league_id


def get_team_played_matches_count(league_id: int, team_id: int) -> int:
    row = execute_query(
        """
        SELECT COUNT(*) AS cnt
        FROM matches
        WHERE league_id = ?
          AND status = 'played'
          AND home_goals IS NOT NULL
          AND away_goals IS NOT NULL
          AND (home_club_id = ? OR away_club_id = ?)
        """,
        (league_id, team_id, team_id),
        fetchone=True,
    )
    return int(row["cnt"]) if row else 0


def _played_matches_in_league(league_id: int) -> List[Dict[str, object]]:
    rows = execute_query(
        """
        SELECT id, round_no, home_club_id, away_club_id, home_goals, away_goals
        FROM matches
        WHERE league_id = ?
          AND status = 'played'
          AND home_goals IS NOT NULL
          AND away_goals IS NOT NULL
        ORDER BY round_no ASC, id ASC
        """,
        (league_id,),
        fetchall=True,
    )
    return [dict(r) for r in (rows or [])]


def _safe_avg(goals: int, matches: int) -> float:
    return (goals / matches) if matches > 0 else 0.0


def _form_ratio(last_points: Sequence[int]) -> float:
    if not last_points:
        return 0.0
    return float(sum(last_points)) / float(len(last_points) * 3)


def _feature_vector(home: TeamState, away: TeamState) -> List[float]:
    home_gd = home.goals_for - home.goals_against
    away_gd = away.goals_for - away.goals_against

    return [
        float(home.points - away.points),
        float(home_gd - away_gd),
        _safe_avg(home.goals_for, home.matches),
        _safe_avg(away.goals_for, away.matches),
        _form_ratio(list(home.form_points)) - _form_ratio(list(away.form_points)),
    ]


def _update_team_state(state: TeamState, goals_for: int, goals_against: int) -> None:
    state.matches += 1
    state.goals_for += goals_for
    state.goals_against += goals_against
    if goals_for > goals_against:
        state.points += 3
        state.form_points.append(3)
    elif goals_for == goals_against:
        state.points += 1
        state.form_points.append(1)
    else:
        state.form_points.append(0)


def build_training_dataset(league_id: int) -> Tuple[List[List[float]], List[int]]:
    matches = _played_matches_in_league(league_id)
    states: Dict[int, TeamState] = {}
    features: List[List[float]] = []
    labels: List[int] = []

    for m in matches:
        home_id = int(m["home_club_id"])
        away_id = int(m["away_club_id"])
        hg = int(m["home_goals"])
        ag = int(m["away_goals"])

        home_state = states.setdefault(home_id, TeamState())
        away_state = states.setdefault(away_id, TeamState())

        features.append(_feature_vector(home_state, away_state))

        if hg > ag:
            labels.append(0)
        elif hg == ag:
            labels.append(1)
        else:
            labels.append(2)

        _update_team_state(home_state, hg, ag)
        _update_team_state(away_state, ag, hg)

    return features, labels


def build_prediction_features(league_id: int, home_team_id: int, away_team_id: int) -> List[float]:
    matches = _played_matches_in_league(league_id)
    states: Dict[int, TeamState] = {}

    for m in matches:
        home_id = int(m["home_club_id"])
        away_id = int(m["away_club_id"])
        hg = int(m["home_goals"])
        ag = int(m["away_goals"])

        home_state = states.setdefault(home_id, TeamState())
        away_state = states.setdefault(away_id, TeamState())

        _update_team_state(home_state, hg, ag)
        _update_team_state(away_state, ag, hg)

    home_state = states.setdefault(home_team_id, TeamState())
    away_state = states.setdefault(away_team_id, TeamState())
    return _feature_vector(home_state, away_state)
