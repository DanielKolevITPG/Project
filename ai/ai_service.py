from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from ai import features
from ai.model import predict_probabilities


class AIPredictionError(Exception):
    pass


@dataclass
class PredictionResult:
    home_team: str
    away_team: str
    home_win_pct: int
    draw_pct: int
    away_win_pct: int


def _normalize_to_percent(prob_map: Dict[int, float]) -> Dict[int, int]:
    safe = {k: max(0.0, float(v)) for k, v in prob_map.items()}
    total = sum(safe.values())
    if total <= 0:
        safe = {0: 1.0, 1: 1.0, 2: 1.0}
        total = 3.0

    normalized = {k: (v / total) * 100.0 for k, v in safe.items()}

    base = {k: int(normalized[k]) for k in (0, 1, 2)}
    remainder = 100 - sum(base.values())

    # Give missing points to highest fractional parts first
    fractional = sorted(
        ((k, normalized[k] - base[k]) for k in (0, 1, 2)), key=lambda x: x[1], reverse=True
    )
    idx = 0
    while remainder > 0:
        base[fractional[idx % 3][0]] += 1
        remainder -= 1
        idx += 1

    return base


def get_match_prediction(home_team: str, away_team: str) -> PredictionResult:
    home = features.get_team_by_name(home_team)
    away = features.get_team_by_name(away_team)

    if home is None:
        raise AIPredictionError(f"Отборът '{home_team}' не съществува.")
    if away is None:
        raise AIPredictionError(f"Отборът '{away_team}' не съществува.")

    home_id = int(home["id"])
    away_id = int(away["id"])

    league_id = features.get_common_league_id(home_id, away_id)
    if league_id is None:
        raise AIPredictionError("Отборите не са в една и съща лига.")

    home_played = features.get_team_played_matches_count(league_id, home_id)
    away_played = features.get_team_played_matches_count(league_id, away_id)
    if home_played < features.MIN_MATCHES_REQUIRED or away_played < features.MIN_MATCHES_REQUIRED:
        raise AIPredictionError(
            f"Недостатъчно данни. И двата отбора трябва да имат минимум {features.MIN_MATCHES_REQUIRED} изиграни мача."
        )

    train_x, train_y = features.build_training_dataset(league_id)
    if len(train_x) < features.MIN_MATCHES_REQUIRED:
        raise AIPredictionError(
            f"Недостатъчно данни за обучение. Нужни са минимум {features.MIN_MATCHES_REQUIRED} изиграни мача в лигата."
        )

    current_x = features.build_prediction_features(league_id, home_id, away_id)
    probs = predict_probabilities(train_x, train_y, current_x)
    pct = _normalize_to_percent(probs)

    return PredictionResult(
        home_team=str(home["name"]),
        away_team=str(away["name"]),
        home_win_pct=pct[0],
        draw_pct=pct[1],
        away_win_pct=pct[2],
    )
