from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

from src.services import matches_service


def handle_select_league(match: Optional[re.Match]) -> Tuple[str, Dict[str, Any]]:
    if match is None:
        raise ValueError("Missing regex match")
    name = (match.group("name") or "").strip()
    season = (match.group("season") or "").strip()
    params = {"league": name, "season": season}
    msg = matches_service.select_league(name, season)
    return msg, params


def handle_show_round(match: Optional[re.Match]) -> Tuple[str, Dict[str, Any]]:
    if match is None:
        raise ValueError("Missing regex match")
    round_no = int(match.group("round"))
    name = (match.group("name") or "").strip()
    season = (match.group("season") or "").strip()
    # command carries league+season too; we reuse it to set context
    msg1 = matches_service.select_league(name, season)
    msg2 = matches_service.show_round(round_no)
    params = {"round": round_no, "league": name, "season": season}
    return f"{msg1}\n{msg2}", params


def handle_select_match(match: Optional[re.Match]) -> Tuple[str, Dict[str, Any]]:
    if match is None:
        raise ValueError("Missing regex match")
    match_id = int(match.group("match_id"))
    params = {"match_id": match_id}
    msg = matches_service.select_match(match_id)
    return msg, params


def handle_save_result(match: Optional[re.Match]) -> Tuple[str, Dict[str, Any]]:
    if match is None:
        raise ValueError("Missing regex match")
    home = (match.group("home") or "").strip()
    away = (match.group("away") or "").strip()
    hg = int(match.group("home_goals"))
    ag = int(match.group("away_goals"))
    params = {"home": home, "away": away, "home_goals": hg, "away_goals": ag}
    msg = matches_service.save_result_by_teams(home, away, hg, ag)
    return msg, params


def handle_add_goal(match: Optional[re.Match]) -> Tuple[str, Dict[str, Any]]:
    if match is None:
        raise ValueError("Missing regex match")
    rest = (match.group("rest") or "").strip()
    minute = int(match.group("minute"))

    player, club = _split_player_club(rest)
    params = {"player": player, "club": club, "minute": minute}
    msg = matches_service.add_goal(player, club, minute)
    return msg, params


def handle_add_card(match: Optional[re.Match]) -> Tuple[str, Dict[str, Any]]:
    if match is None:
        raise ValueError("Missing regex match")
    rest = (match.group("rest") or "").strip()
    card_type = (match.group("type") or "").strip()
    minute = int(match.group("minute"))

    player, club = _split_player_club(rest)
    params = {"player": player, "club": club, "card_type": card_type, "minute": minute}
    msg = matches_service.add_card(player, club, card_type, minute)
    return msg, params


def _split_player_club(rest: str) -> Tuple[str, str]:
    """Split '<player> <club>' using known club names from DB.

    This avoids ambiguous regex parsing when club names contain spaces.
    """
    if not rest:
        raise ValueError("Липсват играч и отбор.")

    # Try longest club match first
    # Query directly; avoids dependency on runtime context.
    from src.db import execute_query

    rows = execute_query(
        "SELECT name FROM clubs ORDER BY LENGTH(name) DESC", fetchall=True
    )
    club_names = [r["name"] for r in (rows or [])]
    rest_l = rest.lower()
    for cn in club_names:
        cn_l = cn.lower()
        if rest_l.endswith(" " + cn_l):
            player = rest[: -(len(cn) + 1)].strip()
            club = cn
            if player:
                return player, club

    raise ValueError("Не успях да разпозная отбора. Формат: <Играч> <Отбор> ...")


def handle_show_events(match: Optional[re.Match]) -> Tuple[str, Dict[str, Any]]:
    match_id = None
    if match is not None:
        mid = match.groupdict().get("match_id")
        match_id = int(mid) if mid else None
    params = {"match_id": match_id}
    msg = matches_service.show_events(match_id)
    return msg, params
