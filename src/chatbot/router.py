import os
import json
import re
from typing import Tuple, Optional, Dict, Any
from src.services.players_service import (
    add_player,
    get_players_by_club_name,
    get_players,
    update_player_number,
    update_player_status,
    delete_player_by_name,
    format_player_list,
)
from src.services import clubs_service
from src.services import transfers_service
from src.services import leagues_service
from src.chatbot import handlers_matches
from src.chatbot import handlers_standings
from src.utils.logger import log_command

INTENTS_FILE = os.path.join(os.path.dirname(__file__), "..", "intents.json")


class Chatbot:
    def __init__(self, intents_path: str = INTENTS_FILE):
        self.intents = {}
        self.compiled = []
        self._load_intents(intents_path)

    def _load_intents(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.intents = json.load(f)
            for name, data in self.intents.items():
                for p in data.get("patterns", []):
                    try:
                        self.compiled.append((name, re.compile(p)))
                    except re.error:
                        continue
        except Exception as e:
            raise RuntimeError(f"Failed to load intents: {e}")

    def handle(self, text: str) -> Tuple[str, bool]:
        text = text.strip()
        if not text:
            return ("Моля въведете команда. (помощ за помощ)", False)

        intent_name, match = self._detect_intent(text)
        if not intent_name:
            return ("Не разбрах командата. (помощ за списък с команди)", False)

        try:
            params: Optional[Dict[str, Any]] = None
            if intent_name == "help":
                response = self.intents[intent_name].get("response", "help")
                log_command(text, intent_name, params, response)
                return (response, False)
            if intent_name == "exit":
                response = self.intents[intent_name].get("response", "exit")
                log_command(text, intent_name, params, response)
                return (response, True)
            if intent_name == "list_clubs":
                clubs = clubs_service.get_all_clubs()
                if not clubs:
                    response = "Няма записани клубове."
                    log_command(text, intent_name, params, response)
                    return (response, False)
                lines = [f"{c['id']}: {c['name']}" for c in clubs]
                response = "\n".join(lines)
                log_command(text, intent_name, params, response)
                return (response, False)
            if intent_name == "add_club":
                name = (self._extract_group(match, "name") or "").strip()
                if not name:
                    response = "Не открих име на клуб. Моля опитайте: Добави клуб <Име>"
                    log_command(text, intent_name, params, response)
                    return (response, False)
                res = clubs_service.add_club(name)
                response = res.get("message", "Неуспешна операция.")
                log_command(text, intent_name, {"name": name}, response)
                return (response, False)
            if intent_name == "delete_club":
                name = (self._extract_group(match, "name") or "").strip()
                if not name:
                    response = "Не открих име на клуб. Моля опитайте: Изтрий клуб <Име>"
                    log_command(text, intent_name, params, response)
                    return (response, False)
                res = clubs_service.delete_club(name)
                response = res.get("message", "Неуспешна операция.")
                log_command(text, intent_name, {"name": name}, response)
                return (response, False)

            if intent_name == "add_player":
                name = (self._extract_group(match, "name") or "").strip()
                club = (self._extract_group(match, "club") or "").strip()
                position = (self._extract_group(match, "position") or "").strip()
                number_str = (self._extract_group(match, "number") or "").strip()
                nationality = (self._extract_group(match, "nationality") or "").strip()
                birth_date = (self._extract_group(match, "birth_date") or "").strip()
                status = (self._extract_group(match, "status") or "").strip()

                if not all([name, club, position, number_str, nationality, birth_date]):
                    response = "Недостатъчно данни. Очакван формат: Добави играч <име> в клуб <клуб> на позиция <GK|DF|MF|FW> с номер <1-99> и националност <националност> и дата на раждане <YYYY-MM-DD> и статус <active|injured|retired>"
                    log_command(
                        text,
                        intent_name,
                        {
                            "name": name,
                            "club": club,
                            "position": position,
                            "number": number_str,
                            "nationality": nationality,
                            "birth_date": birth_date,
                            "status": status,
                        },
                        response,
                    )
                    return (response, False)

                try:
                    number = int(number_str)
                except ValueError:
                    response = "Невалиден номер. Трябва да е число между 1 и 99."
                    log_command(
                        text,
                        intent_name,
                        {"name": name, "number": number_str},
                        response,
                    )
                    return (response, False)

                try:
                    res = add_player(
                        full_name=name,
                        birth_date=birth_date,
                        nationality=nationality,
                        position=position.upper(),
                        number=number,
                        club_name=club,
                    )
                    response = res
                    log_command(
                        text,
                        intent_name,
                        {
                            "name": name,
                            "club": club,
                            "position": position,
                            "number": number,
                            "nationality": nationality,
                            "birth_date": birth_date,
                            "status": status,
                        },
                        response,
                    )
                    return (response, False)
                except Exception as e:
                    response = f"Грешка при добавяне на играч: {e}"
                    log_command(
                        text, intent_name, {"name": name, "club": club}, response
                    )
                    return (response, False)

            if intent_name == "list_players":
                club = (self._extract_group(match, "club") or "").strip()
                if club:
                    try:
                        players = get_players_by_club_name(club)
                        formatted = format_player_list(players)
                        response = (
                            formatted if formatted else "Няма играчи в този клуб."
                        )
                        log_command(text, intent_name, {"club": club}, response)
                        return (response, False)
                    except Exception as e:
                        response = f"Грешка: {e}"
                        log_command(text, intent_name, {"club": club}, response)
                        return (response, False)
                else:
                    all_players = get_players()
                    formatted = format_player_list(all_players)
                    response = formatted if formatted else "Няма записани играчи."
                    log_command(text, intent_name, params, response)
                    return (response, False)

            if intent_name == "update_player_number":
                name = (self._extract_group(match, "name") or "").strip()
                number_str = (self._extract_group(match, "number") or "").strip()

                if not name or not number_str:
                    response = "Не открих име или номер. Моля опитайте: Смени номер на <име> на <номер>"
                    log_command(
                        text,
                        intent_name,
                        {"name": name, "number": number_str},
                        response,
                    )
                    return (response, False)

                try:
                    number = int(number_str)
                except ValueError:
                    response = "Невалиден номер."
                    log_command(
                        text,
                        intent_name,
                        {"name": name, "number": number_str},
                        response,
                    )
                    return (response, False)

                try:
                    res = update_player_number(name, number)
                    response = res
                    log_command(
                        text, intent_name, {"name": name, "number": number}, response
                    )
                    return (response, False)
                except Exception as e:
                    response = f"Грешка при актуализация: {e}"
                    log_command(
                        text,
                        intent_name,
                        {"name": name, "number": number_str},
                        response,
                    )
                    return (response, False)

            if intent_name == "update_player_status":
                name = (self._extract_group(match, "name") or "").strip()
                status = (self._extract_group(match, "status") or "").strip()

                if not name or not status:
                    response = "Не открих име или статус. Моля опитайте: Смени статус на <име> на <active|injured|retired>"
                    log_command(
                        text, intent_name, {"name": name, "status": status}, response
                    )
                    return (response, False)

                try:
                    res = update_player_status(name, status)
                    response = res
                    log_command(
                        text, intent_name, {"name": name, "status": status}, response
                    )
                    return (response, False)
                except Exception as e:
                    response = f"Грешка при актуализация: {e}"
                    log_command(
                        text, intent_name, {"name": name, "status": status}, response
                    )
                    return (response, False)

            if intent_name == "delete_player":
                name = (self._extract_group(match, "name") or "").strip()
                if not name:
                    response = (
                        "Не открих име на играч. Моля опитайте: Изтрий играч <име>"
                    )
                    log_command(text, intent_name, params, response)
                    return (response, False)

                try:
                    res = delete_player_by_name(name)
                    response = res
                    log_command(text, intent_name, {"name": name}, response)
                    return (response, False)
                except Exception as e:
                    response = f"Грешка при изтриване: {e}"
                    log_command(text, intent_name, {"name": name}, response)
                    return (response, False)

            if intent_name == "transfer_player":
                player_name = (self._extract_group(match, "player") or "").strip()
                from_club = (self._extract_group(match, "from_club") or "").strip()
                to_club = (self._extract_group(match, "to_club") or "").strip()
                date = (self._extract_group(match, "date") or "").strip()
                fee_str = (self._extract_group(match, "fee") or "").strip() or None

                if not all([player_name, from_club, to_club, date]):
                    response = "Недостатъчно данни. Очакван формат: Трансфер <име> от <клуб> в <клуб> <YYYY-MM-DD> [сума <сума>]"
                    log_command(
                        text,
                        intent_name,
                        {
                            "player": player_name,
                            "from_club": from_club,
                            "to_club": to_club,
                            "date": date,
                            "fee": fee_str,
                        },
                        response,
                    )
                    return (response, False)

                try:
                    fee = int(fee_str) if fee_str else None
                except ValueError:
                    response = "Невалидна сума."
                    log_command(
                        text,
                        intent_name,
                        {"player": player_name, "fee": fee_str},
                        response,
                    )
                    return (response, False)

                try:
                    res = transfers_service.transfer_player(
                        player_name=player_name,
                        from_club=from_club,
                        to_club=to_club,
                        date=date,
                        fee=fee,
                    )
                    response = res
                    log_command(
                        text,
                        intent_name,
                        {
                            "player": player_name,
                            "from_club": from_club,
                            "to_club": to_club,
                            "date": date,
                            "fee": fee,
                        },
                        response,
                    )
                    return (response, False)
                except Exception as e:
                    response = f"Грешка при трансфер: {e}"
                    log_command(text, intent_name, {"player": player_name}, response)
                    return (response, False)

            if intent_name == "show_transfers_player":
                player_name = (self._extract_group(match, "player") or "").strip()
                if not player_name:
                    response = "Не открих име на играч. Очакван формат: Покажи трансфери на <име>"
                    log_command(text, intent_name, params, response)
                    return (response, False)

                try:
                    res = transfers_service.list_transfers_by_player(player_name)
                    response = res
                    log_command(text, intent_name, {"player": player_name}, response)
                    return (response, False)
                except Exception as e:
                    response = f"Грешка: {e}"
                    log_command(text, intent_name, {"player": player_name}, response)
                    return (response, False)

            if intent_name == "show_transfers_club":
                club_name = (self._extract_group(match, "club") or "").strip()
                if not club_name:
                    response = "Не открих име на клуб. Очакван формат: Покажи трансфери на <клуб>"
                    log_command(text, intent_name, params, response)
                    return (response, False)

                try:
                    res = transfers_service.list_transfers_by_club(club_name)
                    response = res
                    log_command(text, intent_name, {"club": club_name}, response)
                    return (response, False)
                except Exception as e:
                    response = f"Грешка: {e}"
                    log_command(text, intent_name, {"club": club_name}, response)
                    return (response, False)

            # League intents
            if intent_name == "create_league":
                name = (self._extract_group(match, "name") or "").strip()
                season = (self._extract_group(match, "season") or "").strip()

                if not name or not season:
                    response = "Недостатъчно данни. Очакван формат: Създай лига <име> <сезон> (напр. 2025/2026)"
                    log_command(
                        text, intent_name, {"name": name, "season": season}, response
                    )
                    return (response, False)

                try:
                    res = leagues_service.create_league(name, season)
                    response = res
                    log_command(
                        text, intent_name, {"name": name, "season": season}, response
                    )
                    return (response, False)
                except Exception as e:
                    response = f"Грешка при създаване на лига: {e}"
                    log_command(
                        text, intent_name, {"name": name, "season": season}, response
                    )
                    return (response, False)

            if intent_name == "add_team_to_league":
                club = (self._extract_group(match, "club") or "").strip()
                name = (self._extract_group(match, "name") or "").strip()
                season = (self._extract_group(match, "season") or "").strip()

                if not all([club, name, season]):
                    response = "Недостатъчно данни. Очакван формат: Добави отбор <клуб> в лига <име> <сезон>"
                    log_command(
                        text,
                        intent_name,
                        {"club": club, "name": name, "season": season},
                        response,
                    )
                    return (response, False)

                try:
                    res = leagues_service.add_team_to_league(name, season, club)
                    response = res
                    log_command(
                        text,
                        intent_name,
                        {"club": club, "name": name, "season": season},
                        response,
                    )
                    return (response, False)
                except Exception as e:
                    response = f"Грешка при добавяне на отбор: {e}"
                    log_command(
                        text,
                        intent_name,
                        {"club": club, "name": name, "season": season},
                        response,
                    )
                    return (response, False)

            if intent_name == "remove_team_from_league":
                club = (self._extract_group(match, "club") or "").strip()
                name = (self._extract_group(match, "name") or "").strip()
                season = (self._extract_group(match, "season") or "").strip()

                if not all([club, name, season]):
                    response = "Недостатъчно данни. Очакван формат: Премахни отбор <клуб> от лига <име> <сезон>"
                    log_command(
                        text,
                        intent_name,
                        {"club": club, "name": name, "season": season},
                        response,
                    )
                    return (response, False)

                try:
                    res = leagues_service.remove_team_from_league(name, season, club)
                    response = res
                    log_command(
                        text,
                        intent_name,
                        {"club": club, "name": name, "season": season},
                        response,
                    )
                    return (response, False)
                except Exception as e:
                    response = f"Грешка при премахване на отбор: {e}"
                    log_command(
                        text,
                        intent_name,
                        {"club": club, "name": name, "season": season},
                        response,
                    )
                    return (response, False)

            if intent_name == "show_teams_in_league":
                name = (self._extract_group(match, "name") or "").strip()
                season = (self._extract_group(match, "season") or "").strip()

                if not name or not season:
                    response = "Недостатъчно данни. Очакван формат: Покажи отбори в лига <име> <сезон>"
                    log_command(
                        text, intent_name, {"name": name, "season": season}, response
                    )
                    return (response, False)

                try:
                    res = leagues_service.get_teams_in_league(name, season)
                    response = res
                    log_command(
                        text, intent_name, {"name": name, "season": season}, response
                    )
                    return (response, False)
                except Exception as e:
                    response = f"Грешка: {e}"
                    log_command(
                        text, intent_name, {"name": name, "season": season}, response
                    )
                    return (response, False)

            if intent_name == "generate_schedule":
                name = (self._extract_group(match, "name") or "").strip()
                season = (self._extract_group(match, "season") or "").strip()

                if not name or not season:
                    response = "Недостатъчно данни. Очакван формат: Генерирай програма <име> <сезон>"
                    log_command(
                        text, intent_name, {"name": name, "season": season}, response
                    )
                    return (response, False)

                try:
                    res = leagues_service.generate_round_robin_schedule(name, season)
                    response = res
                    log_command(
                        text, intent_name, {"name": name, "season": season}, response
                    )
                    return (response, False)
                except Exception as e:
                    response = f"Грешка при генериране на програма: {e}"
                    log_command(
                        text, intent_name, {"name": name, "season": season}, response
                    )
                    return (response, False)

            if intent_name == "show_schedule":
                name = (self._extract_group(match, "name") or "").strip()
                season = (self._extract_group(match, "season") or "").strip()

                if not name or not season:
                    response = "Недостатъчно данни. Очакван формат: Покажи програма <име> <сезон>"
                    log_command(
                        text, intent_name, {"name": name, "season": season}, response
                    )
                    return (response, False)

                try:
                    res = leagues_service.get_league_schedule(name, season)
                    response = res
                    log_command(
                        text, intent_name, {"name": name, "season": season}, response
                    )
                    return (response, False)
                except Exception as e:
                    response = f"Грешка: {e}"
                    log_command(
                        text, intent_name, {"name": name, "season": season}, response
                    )
                    return (response, False)

            if intent_name == "delete_league":
                name = (self._extract_group(match, "name") or "").strip()
                season = (self._extract_group(match, "season") or "").strip()

                if not name or not season:
                    response = (
                        "Недостатъчно данни. Очакван формат: Изтрий лига <име> <сезон>"
                    )
                    log_command(
                        text, intent_name, {"name": name, "season": season}, response
                    )
                    return (response, False)

                try:
                    res = leagues_service.delete_league(name, season)
                    response = res
                    log_command(
                        text, intent_name, {"name": name, "season": season}, response
                    )
                    return (response, False)
                except Exception as e:
                    response = f"Грешка при изтриване на лига: {e}"
                    log_command(
                        text, intent_name, {"name": name, "season": season}, response
                    )
                    return (response, False)

            # Matches intents
            if intent_name == "select_league":
                if not match:
                    response = "Невалиден формат. Очаква се: Избери лига <име> <сезон>."
                    log_command(text, intent_name, None, response)
                    return (response, False)
                response, params = handlers_matches.handle_select_league(match)
                log_command(text, intent_name, params, response)
                return (response, False)

            if intent_name == "show_round":
                if not match:
                    response = (
                        "Невалиден формат. Очаква се: Покажи кръг <N> <лига> <сезон>."
                    )
                    log_command(text, intent_name, None, response)
                    return (response, False)
                response, params = handlers_matches.handle_show_round(match)
                log_command(text, intent_name, params, response)
                return (response, False)

            if intent_name == "select_match":
                if not match:
                    response = "Невалиден формат. Очаква се: Избери мач <match_id>."
                    log_command(text, intent_name, None, response)
                    return (response, False)
                response, params = handlers_matches.handle_select_match(match)
                log_command(text, intent_name, params, response)
                return (response, False)

            if intent_name == "save_result":
                if not match:
                    response = "Невалиден формат. Очаква се: Резултат <Домакин>-<Гост> <X>:<Y> запиши."
                    log_command(text, intent_name, None, response)
                    return (response, False)
                response, params = handlers_matches.handle_save_result(match)
                log_command(text, intent_name, params, response)
                return (response, False)

            if intent_name == "add_goal":
                if not match:
                    response = "Невалиден формат. Очаква се: Гол <Играч> <Отбор> <минута> минута."
                    log_command(text, intent_name, None, response)
                    return (response, False)
                response, params = handlers_matches.handle_add_goal(match)
                log_command(text, intent_name, params, response)
                return (response, False)

            if intent_name == "add_card":
                if not match:
                    response = "Невалиден формат. Очаква се: Картон <Играч> <Отбор> <Y/R> <минута>."
                    log_command(text, intent_name, None, response)
                    return (response, False)
                response, params = handlers_matches.handle_add_card(match)
                log_command(text, intent_name, params, response)
                return (response, False)

            if intent_name == "show_events":
                response, params = handlers_matches.handle_show_events(match)
                log_command(text, intent_name, params, response)
                return (response, False)

            if intent_name == "show_standings":
                if not match:
                    response = "Невалиден формат. Очаква се: Покажи класиране <лига> <сезон>."
                    log_command(text, intent_name, None, response)
                    return (response, False)
                response, params = handlers_standings.handle_show_standings(match)
                log_command(text, intent_name, params, response)
                return (response, False)

            if intent_name == "refresh_standings":
                response, params = handlers_standings.handle_refresh_standings(match)
                log_command(text, intent_name, params, response)
                return (response, False)

        except Exception as e:
            response = f"Възникна грешка при обработка: {e}"
            log_command(text, intent_name, None, response)
            return (response, False)

        return ("Командата е разпозната, но няма обработчик.", False)

    def _detect_intent(self, text: str) -> Tuple[Optional[str], Optional[re.Match]]:
        for name, regex in self.compiled:
            m = regex.search(text)
            if m:
                return (name, m)
        return (None, None)

    def _extract_group(self, match: Optional[re.Match], group: str) -> Optional[str]:
        if not match:
            return None
        try:
            g = match.group(group)
            return g.strip() if g else None
        except IndexError:
            return None


bot = Chatbot()
