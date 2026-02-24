import json
import os
import re
from typing import Tuple, Optional

# ...existing code...
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