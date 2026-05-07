from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.repositories import standings_repo


class StandingsError(Exception):
    pass


class ValidationError(StandingsError):
    pass


class NotFoundError(StandingsError):
    pass


@dataclass
class TeamStanding:
    club_id: int
    club_name: str
    mp: int = 0
    w: int = 0
    d: int = 0
    l: int = 0
    gf: int = 0
    ga: int = 0
    gd: int = 0
    pts: int = 0


def get_standings(league_name: str, season: str) -> str:
    if not league_name or not league_name.strip():
        raise ValidationError("Липсва име на лига.")
    if not season or not season.strip():
        raise ValidationError("Липсва сезон.")

    league_id = standings_repo.get_league_id_by_name_season(
        league_name.strip(), season.strip()
    )
    if league_id is None:
        raise NotFoundError(f"Няма лига '{league_name}' сезон {season}.")

    teams = standings_repo.get_teams_in_league(league_id)
    if not teams:
        raise ValidationError(f"Няма отбори в лигата '{league_name}' {season}.")

    matches = standings_repo.get_played_matches_for_league(league_id)

    team_data: Dict[int, TeamStanding] = {}
    for team in teams:
        team_data[team["id"]] = TeamStanding(
            club_id=team["id"], club_name=team["name"]
        )

    for match in matches:
        home_id = match["home_club_id"]
        away_id = match["away_club_id"]
        home_goals = match["home_goals"]
        away_goals = match["away_goals"]

        if home_id not in team_data or away_id not in team_data:
            continue

        home = team_data[home_id]
        away = team_data[away_id]

        home.mp += 1
        away.mp += 1
        home.gf += home_goals
        home.ga += away_goals
        away.gf += away_goals
        away.ga += home_goals

        if home_goals > away_goals:
            home.w += 1
            home.pts += 3
            away.l += 1
        elif home_goals < away_goals:
            away.w += 1
            away.pts += 3
            home.l += 1
        else:
            home.d += 1
            away.d += 1
            home.pts += 1
            away.pts += 1

    for team in team_data.values():
        team.gd = team.gf - team.ga

    standings_list = sorted(
        team_data.values(),
        key=lambda t: (-t.pts, -t.gd, -t.gf, t.club_name),
    )

    return _format_standings(
        standings_list, league_name.strip(), season.strip(), len(matches)
    )


def get_standings_with_h2h(league_name: str, season: str, use_h2h: bool = True) -> str:
    if not league_name or not league_name.strip():
        raise ValidationError("Липсва име на лига.")
    if not season or not season.strip():
        raise ValidationError("Липсва сезон.")

    league_id = standings_repo.get_league_id_by_name_season(
        league_name.strip(), season.strip()
    )
    if league_id is None:
        raise NotFoundError(f"Няма лига '{league_name}' сезон {season}.")

    teams = standings_repo.get_teams_in_league(league_id)
    if not teams:
        raise ValidationError(f"Няма отбори в лигата '{league_name}' {season}.")

    matches = standings_repo.get_played_matches_for_league(league_id)

    team_data: Dict[int, TeamStanding] = {}
    for team in teams:
        team_data[team["id"]] = TeamStanding(
            club_id=team["id"], club_name=team["name"]
        )

    for match in matches:
        home_id = match["home_club_id"]
        away_id = match["away_club_id"]
        home_goals = match["home_goals"]
        away_goals = match["away_goals"]

        if home_id not in team_data or away_id not in team_data:
            continue

        home = team_data[home_id]
        away = team_data[away_id]

        home.mp += 1
        away.mp += 1
        home.gf += home_goals
        home.ga += away_goals
        away.gf += away_goals
        away.ga += home_goals

        if home_goals > away_goals:
            home.w += 1
            home.pts += 3
            away.l += 1
        elif home_goals < away_goals:
            away.w += 1
            away.pts += 3
            home.l += 1
        else:
            home.d += 1
            away.d += 1
            home.pts += 1
            away.pts += 1

    for team in team_data.values():
        team.gd = team.gf - team.ga

    standings_list = list(team_data.values())

    if use_h2h:
        h2h_matches = standings_repo.get_head_to_head_matches(
            league_id, [t.club_id for t in standings_list]
        )

        h2h_pts: Dict[int, Dict[int, int]] = {
            tid: {tid2: 0 for tid2 in team_data.keys()} for tid in team_data.keys()
        }
        h2h_gd: Dict[int, Dict[int, int]] = {
            tid: {tid2: 0 for tid2 in team_data.keys()} for tid in team_data.keys()
        }
        h2h_gf: Dict[int, Dict[int, int]] = {
            tid: {tid2: 0 for tid2 in team_data.keys()} for tid in team_data.keys()
        }

        for match in h2h_matches:
            h_id = match["home_club_id"]
            a_id = match["away_club_id"]
            hg = match["home_goals"]
            ag = match["away_goals"]

            h2h_gf[h_id][a_id] += hg
            h2h_gf[a_id][h_id] += ag
            h2h_gd[h_id][a_id] += hg - ag
            h2h_gd[a_id][h_id] += ag - hg

            if hg > ag:
                h2h_pts[h_id][a_id] += 3
            elif hg < ag:
                h2h_pts[a_id][h_id] += 3
            else:
                h2h_pts[h_id][a_id] += 1
                h2h_pts[a_id][h_id] += 1

        def h2h_sort_key(t: TeamStanding) -> tuple:
            h2h_points = 0
            h2h_goal_diff = 0
            h2h_goals_for = 0
            for other in standings_list:
                if t.club_id == other.club_id:
                    continue
                h2h_points += h2h_pts[t.club_id].get(other.club_id, 0)
                h2h_goal_diff += h2h_gd[t.club_id].get(other.club_id, 0)
                h2h_goals_for += h2h_gf[t.club_id].get(other.club_id, 0)
            return (-t.pts, -t.gd, -t.gf, -h2h_points, -h2h_goal_diff, -h2h_goals_for, t.club_name)

        standings_list = sorted(standings_list, key=h2h_sort_key)
    else:
        standings_list = sorted(
            standings_list,
            key=lambda t: (-t.pts, -t.gd, -t.gf, t.club_name),
        )

    return _format_standings(
        standings_list, league_name.strip(), season.strip(), len(matches)
    )


def _format_standings(
    standings: List[TeamStanding],
    league_name: str,
    season: str,
    match_count: int,
) -> str:
    if match_count == 0:
        lines = [f"Класиране — {league_name} {season} (няма изиграни мачове):"]
        for pos, t in enumerate(standings, 1):
            lines.append(
                f"{pos}. {t.club_name} 0 0 0 0 0:0 0"
            )
        return "\n".join(lines)

    lines = [f"Класиране — {league_name} {season} ({match_count} изиграни мача):"]
    for pos, t in enumerate(standings, 1):
        sign = "+" if t.gd > 0 else "" if t.gd == 0 else ""
        lines.append(
            f"{pos}. {t.club_name} {t.mp} {t.w} {t.d} {t.l} {t.gf}:{t.ga} {sign}{t.gd} {t.pts}"
        )
    return "\n".join(lines)