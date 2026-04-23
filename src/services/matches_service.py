from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from src.db import get_connection

from src.repositories import matches_repo


class MatchesError(Exception):
    pass


class ValidationError(MatchesError):
    pass


class NotFoundError(MatchesError):
    pass


@dataclass
class MatchContext:
    league_id: int
    league_name: str
    season: str
    current_match_id: Optional[int] = None


# Runtime context (approach 1 from requirements)
_context: Optional[MatchContext] = None


def get_context() -> Optional[MatchContext]:
    return _context


def select_league(name: str, season: str) -> str:
    global _context

    if not name or not name.strip():
        raise ValidationError("Липсва име на лига.")
    if not season or not season.strip():
        raise ValidationError("Липсва сезон.")

    league_id = matches_repo.get_league_id_by_name_season(name.strip(), season.strip())
    if league_id is None:
        raise NotFoundError(f"Няма лига '{name}' сезон {season}.")

    _context = MatchContext(
        league_id=league_id, league_name=name.strip(), season=season.strip()
    )
    return f"Избрана лига: {name.strip()} {season.strip()} (ID: {league_id})."


def select_match(match_id: int) -> str:
    global _context
    if _context is None:
        raise ValidationError("Първо изберете лига: Избери лига <име> <сезон>.")

    m = matches_repo.get_match_by_id(match_id)
    if not m:
        raise NotFoundError(f"Няма мач с ID {match_id}.")
    if int(m["league_id"]) != int(_context.league_id):
        raise ValidationError(
            f"Мач #{match_id} не е в избраната лига ({_context.league_name} {_context.season})."
        )

    _context.current_match_id = int(match_id)
    return (
        f"Избран мач: #{m['id']} {m['home_name']}–{m['away_name']} "
        f"(кръг {m['round_no']}, статус {m['status']})."
    )


def show_round(round_no: int) -> str:
    if round_no <= 0:
        raise ValidationError("Невалиден кръг. Очаква се положително число.")
    if _context is None:
        raise ValidationError("Първо изберете лига: Избери лига <име> <сезон>.")

    matches = matches_repo.list_round_matches(_context.league_id, round_no)
    if not matches:
        return f"Няма мачове за кръг {round_no} в '{_context.league_name}' {_context.season}."

    lines = [f"Кръг {round_no} — {_context.league_name} {_context.season}:"]
    for m in matches:
        score = ""
        if m["home_goals"] is not None and m["away_goals"] is not None:
            score = f" {m['home_goals']}:{m['away_goals']}"
        lines.append(
            f"  #{m['id']} {m['home_name']}–{m['away_name']} | {m['status']}{score}"
        )
    return "\n".join(lines)


def _require_context() -> MatchContext:
    if _context is None:
        raise ValidationError("Първо изберете лига: Избери лига <име> <сезон>.")
    return _context


def save_result_by_teams(
    home_name: str, away_name: str, home_goals: int, away_goals: int
) -> str:
    ctx = _require_context()

    if home_goals < 0 or away_goals < 0:
        raise ValidationError("Резултатът трябва да е с цели числа >= 0.")

    home_id = matches_repo.find_club_id_by_name(home_name)
    away_id = matches_repo.find_club_id_by_name(away_name)
    if home_id is None:
        raise NotFoundError(f"Няма отбор '{home_name}'.")
    if away_id is None:
        raise NotFoundError(f"Няма отбор '{away_name}'.")

    matches = matches_repo.find_matches_by_teams_in_league(
        ctx.league_id, home_id, away_id
    )
    if len(matches) == 0:
        raise NotFoundError(
            f"Няма мач {home_name}–{away_name} в избраната лига ({ctx.league_name} {ctx.season})."
        )
    if len(matches) > 1:
        ids = ", ".join([str(m["id"]) for m in matches])
        raise ValidationError(
            f"Има повече от 1 мач {home_name}–{away_name} в този контекст. Изберете мач: {ids}."
        )

    m = matches[0]
    if m["status"] == "played":
        raise ValidationError(
            f"Мач #{m['id']} вече е played. (Ако искате редакция, добавете отделна команда.)"
        )

    updated = matches_repo.update_match_result(int(m["id"]), home_goals, away_goals)
    if updated == 0:
        raise MatchesError("Неуспешен запис на резултат.")

    return (
        f"Записано: {home_name}–{away_name} {home_goals}:{away_goals} (мач #{m['id']})"
    )


def add_goal(player_name: str, club_name: str, minute: int) -> str:
    ctx = _require_context()
    if ctx.current_match_id is None:
        raise ValidationError(
            "Няма избран текущ мач. Използвайте: Избери мач <match_id>."
        )
    if minute < 1 or minute > 120:
        raise ValidationError("Невалидна минута. Очаква се 1–120.")

    club_id = matches_repo.find_club_id_by_name(club_name)
    if club_id is None:
        raise NotFoundError(f"Няма отбор '{club_name}'.")

    participants = matches_repo.get_match_participant_club_ids(ctx.current_match_id)
    if participants is None:
        raise NotFoundError(f"Няма мач #{ctx.current_match_id}.")
    if club_id not in participants:
        raise ValidationError("Отборът не участва в избрания мач.")

    player = matches_repo.find_player_by_name_and_club(player_name, club_id)
    if player is None:
        raise NotFoundError(f"Няма играч '{player_name}' в '{club_name}'.")

    conn = get_connection()
    try:
        goal_id = matches_repo.insert_goal(
            match_id=ctx.current_match_id,
            player_id=int(player["id"]),
            club_id=int(club_id),
            minute=int(minute),
        )
        matches_repo.commit(conn)
    except Exception:
        matches_repo.rollback(conn)
        raise

    return f"Гол записан (ID: {goal_id}) — {player_name} ({club_name}) {minute} минута."


def add_card(player_name: str, club_name: str, card_type: str, minute: int) -> str:
    ctx = _require_context()
    if ctx.current_match_id is None:
        raise ValidationError(
            "Няма избран текущ мач. Използвайте: Избери мач <match_id>."
        )
    if minute < 1 or minute > 120:
        raise ValidationError("Невалидна минута. Очаква се 1–120.")

    ct = (card_type or "").strip().upper()
    if ct not in ("Y", "R"):
        raise ValidationError("Невалиден тип картон. Използвайте Y или R.")

    club_id = matches_repo.find_club_id_by_name(club_name)
    if club_id is None:
        raise NotFoundError(f"Няма отбор '{club_name}'.")

    participants = matches_repo.get_match_participant_club_ids(ctx.current_match_id)
    if participants is None:
        raise NotFoundError(f"Няма мач #{ctx.current_match_id}.")
    if club_id not in participants:
        raise ValidationError("Отборът не участва в избрания мач.")

    player = matches_repo.find_player_by_name_and_club(player_name, club_id)
    if player is None:
        raise NotFoundError(f"Няма играч '{player_name}' в '{club_name}'.")

    # Level 2 validation (selected): 1 red max; 2 yellows => automatic red
    match_id = int(ctx.current_match_id)
    player_id = int(player["id"])

    if matches_repo.count_red_cards_for_player(match_id, player_id) > 0:
        raise ValidationError("Играчът вече има червен картон в този мач.")

    conn = get_connection()
    try:
        if ct == "Y":
            y_cnt = matches_repo.count_yellow_cards_for_player(match_id, player_id)
            if y_cnt >= 2:
                raise ValidationError("Играчът вече има 2 жълти картона в този мач.")

            card_id = matches_repo.insert_card(
                match_id=match_id,
                player_id=player_id,
                club_id=int(club_id),
                card_type="Y",
                minute=int(minute),
            )

            # If this was the 2nd yellow, add automatic red
            if y_cnt + 1 == 2:
                matches_repo.insert_card(
                    match_id=match_id,
                    player_id=player_id,
                    club_id=int(club_id),
                    card_type="R",
                    minute=int(minute),
                )
                matches_repo.commit(conn)
                return (
                    f"Картон записан (ID: {card_id}) — {player_name} ({club_name}) Y {minute}. "
                    f"Автоматично: червен картон (2 жълти)."
                )

            matches_repo.commit(conn)
            return f"Картон записан (ID: {card_id}) — {player_name} ({club_name}) Y {minute}."

        # ct == 'R'
        card_id = matches_repo.insert_card(
            match_id=match_id,
            player_id=player_id,
            club_id=int(club_id),
            card_type="R",
            minute=int(minute),
        )
        matches_repo.commit(conn)
        return (
            f"Картон записан (ID: {card_id}) — {player_name} ({club_name}) R {minute}."
        )
    except Exception:
        matches_repo.rollback(conn)
        raise


def show_events(match_id: Optional[int] = None) -> str:
    ctx = _require_context()
    mid = int(match_id) if match_id is not None else ctx.current_match_id
    if mid is None:
        raise ValidationError(
            "Няма избран текущ мач. Използвайте: Избери мач <match_id>."
        )

    m = matches_repo.get_match_by_id(mid)
    if not m:
        raise NotFoundError(f"Няма мач #{mid}.")
    if int(m["league_id"]) != int(ctx.league_id):
        raise ValidationError("Мачът не е в избраната лига.")

    events = matches_repo.list_match_events(mid)
    if not events:
        return f"Няма събития за мач #{mid} ({m['home_name']}–{m['away_name']})."

    lines = [f"Събития за мач #{mid} ({m['home_name']}–{m['away_name']}):"]
    for e in events:
        if e["event_type"] == "GOAL":
            lines.append(f"  {e['minute']}' Гол: {e['player_name']} ({e['club_name']})")
        else:
            lines.append(
                f"  {e['minute']}' Картон {e['card_type']}: {e['player_name']} ({e['club_name']})"
            )
    return "\n".join(lines)
