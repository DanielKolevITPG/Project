from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

from src.services import standings_service


def handle_show_standings(
    match: Optional[re.Match],
) -> Tuple[str, Dict[str, Any]]:
    if match is None:
        raise ValueError("Missing regex match")

    name = (match.group("name") or "").strip()
    season = (match.group("season") or "").strip()

    params = {"league": name, "season": season}

    try:
        msg = standings_service.get_standings(name, season)
    except standings_service.ValidationError as e:
        msg = f"Грешка: {e}"
    except standings_service.NotFoundError as e:
        msg = f"Грешка: {e}"
    except Exception as e:
        msg = f"Възникна грешка: {e}"

    return msg, params


def handle_refresh_standings(
    match: Optional[re.Match],
) -> Tuple[str, Dict[str, Any]]:
    from src.services import matches_service

    ctx = matches_service.get_context()
    if ctx is None:
        return (
            "Няма избрана лига. Първо изберете лига: Избери лига <име> <сезон>.",
            {},
        )

    params = {"league": ctx.league_name, "season": ctx.season}

    try:
        msg = standings_service.get_standings(ctx.league_name, ctx.season)
    except Exception as e:
        msg = f"Грешка при обновяване на класирането: {e}"

    return msg, params