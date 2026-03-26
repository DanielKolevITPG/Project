import os
import json
import re
from typing import Tuple, Optional, Dict, Any

INTENTS_FILE = os.path.join(os.path.dirname(__file__), "..", "intents.json")


class NLU:
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

    def detect_intent(self, text: str) -> Tuple[Optional[str], Optional[re.Match]]:
        """
        Detect intent from input text.
        
        Returns:
            Tuple of (intent_name, match_object)
        """
        text = text.strip()
        if not text:
            return (None, None)
            
        for name, regex in self.compiled:
            m = regex.search(text)
            if m:
                return (name, m)
        return (None, None)

    def extract_entity(self, match: re.Match, entity: str) -> Optional[str]:
        """
        Extract a named entity from regex match.
        """
        if not match:
            return None
        try:
            g = match.group(entity)
            return g.strip() if g else None
        except IndexError:
            return None

    def get_response(self, intent_name: str) -> str:
        """Get default response for an intent."""
        return self.intents.get(intent_name, {}).get("response", "")
