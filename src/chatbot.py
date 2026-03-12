import json
import os
import re
from typing import Tuple, Optional
from players_service import (
    add_player,
    get_players_by_club_name,
    get_players,
    update_player_number,
    update_player_status,
    delete_player_by_name,
    format_player_list
)
import clubs_service

INTENTS_FILE = os.path.join(os.path.dirname(__file__), "intents.json")


class Chatbot:
    def __init__(self, intents_path: str = INTENTS_FILE):
        self.intents = {}
        self.compiled = []
        self._load_intents(intents_path)

    def _load_intents(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.intents = json.load(f)
            # compile regex patterns
            for name, data in self.intents.items():
                for p in data.get("patterns", []):
                    try:
                        self.compiled.append((name, re.compile(p)))
                    except re.error:
                        # skip invalid regex
                        continue
        except Exception as e:
            raise RuntimeError(f"Failed to load intents: {e}")

    def handle(self, text: str) -> Tuple[str, bool]:
        """
        Process input text -> detect intent via regex -> call handler -> return (response, exit_flag)
        """
        text = text.strip()
        if not text:
            return ("Моля въведете команда. (помощ за помощ)", False)

        intent_name, match = self._detect_intent(text)
        if not intent_name:
            return ("Не разбрах командата. (помощ за списък с команди)", False)

        try:
            if intent_name == "help":
                return (self.intents[intent_name].get("response", "help"), False)
            if intent_name == "exit":
                return (self.intents[intent_name].get("response", "exit"), True)
            if intent_name == "list_clubs":
                clubs = clubs_service.get_all_clubs()
                if not clubs:
                    return ("Няма записани клубове.", False)
                lines = [f"{c['id']}: {c['name']}" for c in clubs]
                return ("\n".join(lines), False)
            if intent_name == "add_club":
                name = self._extract_group(match, "name")
                if not name:
                    return ("Не открих име на клуб. Моля опитайте: Добави клуб <Име>", False)
                res = clubs_service.add_club(name)
                return (res.get("message", "Неуспешна операция."), False)
            if intent_name == "delete_club":
                name = self._extract_group(match, "name")
                if not name:
                    return ("Не открих име на клуб. Моля опитайте: Изтрий клуб <Име>", False)
                res = clubs_service.delete_club(name)
                return (res.get("message", "Неуспешна операция."), False)

            # ADD PLAYER
            if intent_name == "add_player":
                name = self._extract_group(match, "name")
                club = self._extract_group(match, "club")
                position = self._extract_group(match, "position")
                number_str = self._extract_group(match, "number")
                nationality = self._extract_group(match, "nationality")
                birth_date = self._extract_group(match, "birth_date")
                status = self._extract_group(match, "status")

                if not all([name, club, position, number_str, nationality, birth_date]):
                    return ("Недостатъчно данни. Очакван формат: Добави играч <име> в клуб <клуб> на позиция <GK|DF|MF|FW> с номер <1-99> и националност <националност> и дата на раждане <YYYY-MM-DD> и статус <active|injured|retired>", False)

                try:
                    number = int(number_str)
                except ValueError:
                    return ("Невалиден номер. Трябва да е число между 1 и 99.", False)

                try:
                    res = add_player(
                        full_name=name,
                        birth_date=birth_date,
                        nationality=nationality,
                        position=position.upper(),
                        number=number,
                        club_name=club
                    )
                    return (res, False)
                except Exception as e:
                    return (f"Грешка при добавяне на играч: {e}", False)

            # LIST PLAYERS
            if intent_name == "list_players":
                club = self._extract_group(match, "club")
                if club:
                    try:
                        players = get_players_by_club_name(club)
                        formatted = format_player_list(players)
                        return (formatted if formatted else "Няма играчи в този клуб.", False)
                    except Exception as e:
                        return (f"Грешка: {e}", False)
                else:
                    # List all players
                    all_players = get_players()
                    formatted = format_player_list(all_players)
                    return (formatted if formatted else "Няма записани играчи.", False)

            # UPDATE PLAYER NUMBER
            if intent_name == "update_player_number":
                name = self._extract_group(match, "name")
                number_str = self._extract_group(match, "number")

                if not name or not number_str:
                    return ("Не открих име или номер. Моля опитайте: Смени номер на <име> на <номер>", False)

                try:
                    number = int(number_str)
                except ValueError:
                    return ("Невалиден номер.", False)

                try:
                    res = update_player_number(name, number)
                    return (res, False)
                except Exception as e:
                    return (f"Грешка при актуализация: {e}", False)

            # UPDATE PLAYER STATUS
            if intent_name == "update_player_status":
                name = self._extract_group(match, "name")
                status = self._extract_group(match, "status")

                if not name or not status:
                    return ("Не открих име или статус. Моля опитайте: Смени статус на <име> на <active|injured|retired>", False)

                try:
                    res = update_player_status(name, status)
                    return (res, False)
                except Exception as e:
                    return (f"Грешка при актуализация: {e}", False)

            # DELETE PLAYER
            if intent_name == "delete_player":
                name = self._extract_group(match, "name")
                if not name:
                    return ("Не открих име на играч. Моля опитайте: Изтрий играч <име>", False)

                try:
                    res = delete_player_by_name(name)
                    return (res, False)
                except Exception as e:
                    return (f"Грешка при изтриване: {e}", False)

        except Exception as e:
            return (f"Възникна грешка при обработка: {e}", False)

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


# Provide a module-level chatbot instance for main to use
bot = Chatbot()
