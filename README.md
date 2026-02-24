# Football Manager — Stage 2 (Python ↔ SQL + CRUD + Chatbot)

Simple command-line chatbot to manage football clubs (SQLite backend).

Installation
1. Ensure Python 3.8+ is installed.
2. From project root run:
   python src\main.py

The first run will create data.db and apply the SQL schema.

Example commands (Bulgarian)
- Добави клуб Левски София
- Покажи всички клубове
- Изтрий клуб Ботев
- помощ
- изход

Architecture
input -> intent detection (regex, loaded from src/intents.json) -> handler (calls src/clubs_service.py) -> response

Notes:
- All DB access goes through src/db.py.
- Validation enforced in src/clubs_service.py (trim, non-empty, unique).
- Every command is logged to commands.log (timestamp, input, output).
