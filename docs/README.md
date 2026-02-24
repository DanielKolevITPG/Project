# Football Manager — Stage 2 (Python ↔ SQL + CRUD + Chatbot)

Simple command-line chatbot to manage football clubs (SQLite backend).

## Structure
- src/
  - main.py         — entrypoint, main loop and logging
  - db.py           — centralized DB connection + query helper
  - clubs_service.py— Clubs CRUD operations and validation
  - chatbot.py      — intent detection (regex) and handlers
  - intents.json    — regex intent patterns and responses
- sql/
  - schema.sql      — DB schema (clubs table)
- commands.log      — runtime log (created at first run)
- data.db           — SQLite database (created at first run)

## Installation
1. Ensure Python 3.8+
2. Clone repository
3. (Optional) create virtualenv and activate
4. No external packages required

## How to run
From project root (c:\Project-1):
- Windows (PowerShell or cmd):
  python src\main.py

The first run creates data.db and applies schema.

## Example commands (Bulgarian)
- Добави клуб Левски София
- Покажи всички клубове
- Изтрий клуб Ботев
- помощ
- изход

## Architecture
input -> intent detection (regex, loaded from intents.json) -> handler (calls clubs_service) -> response

Notes:
- All DB access goes through src/db.py and clubs_service.py (no SQL in chatbot).
- Validation is enforced in clubs_service (trim, non-empty, unique).
- Every command is logged to commands.log with timestamp, input and output.

## Git commit suggestions (minimal required)
1. initial commit
2. add db module
3. add chatbot base + intents
4. add clubs CRUD
