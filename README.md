# Football Manager — Stage 3 (Players CRUD + Filtering)

Simple command-line chatbot to manage football clubs and players (SQLite backend).

## Structure
- src/
  - main.py         — entrypoint, main loop and logging
  - db.py           — centralized DB connection + query helper
  - clubs_service.py— Clubs CRUD operations and validation
  - players_service.py — Players CRUD operations and validation
  - chatbot.py      — intent detection (regex) and handlers
  - intents.json    — regex intent patterns and responses
- sql/
  - schema.sql      — DB schema (clubs and players tables)
- tests/
  - test_players_service.py — Unit tests for players module
- data/
  - test_players.sql — Sample test data
- commands.log      — runtime log (created at first run)
- data.db           — SQLite database (created at first run)
- dialogue_example.md — Example conversations demonstrating all features

## Installation
1. Ensure Python 3.8+
2. Clone repository
3. (Optional) create virtualenv and activate
4. No external packages required

## How to run
From project root:
- Windows (PowerShell or cmd):
  python src\main.py

The first run creates data.db and applies schema.

## Available Commands (Bulgarian)

### Clubs
- `Добави клуб <Име>` — Add a new club
- `Покажи всички клубове` — List all clubs
- `Изтрий клуб <Име>` — Delete a club

### Players
- `Добави играч <име> в клуб <клуб> на позиция <GK|DF|MF|FW> с номер <1-99> и националност <националност> и дата на раждане <YYYY-MM-DD> и статус <active|injured|retired>` — Add a new player
- `Покажи всички играчи` — List all players
- `Покажи играчи на клуб <клуб>` — List players for a specific club
- `Смени номер на <име> на <номер>` — Update player's jersey number
- `Смени статус на <име> на <active|injured|retired>` — Update player's status
- `Изтрий играч <име>` — Delete a player

### System
- `помощ` or `help` — Show help
- `изход` or `exit` — Exit the application

## Database Schema

### clubs
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `name` TEXT NOT NULL UNIQUE

### players
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `full_name` TEXT NOT NULL
- `birth_date` TEXT NOT NULL (YYYY-MM-DD)
- `nationality` TEXT NOT NULL
- `position` TEXT NOT NULL CHECK(position IN ('GK', 'DF', 'MF', 'FW'))
- `number` INTEGER NOT NULL CHECK(number >= 1 AND number <= 99)
- `status` TEXT NOT NULL DEFAULT 'active'
- `club_id` INTEGER NOT NULL (FK to clubs.id)
- Index on `club_id` for efficient filtering

## Validation Rules

### Player
- **full_name**: Required, non-empty string
- **birth_date**: Required, valid date in the past (YYYY-MM-DD)
- **nationality**: Required, non-empty string
- **position**: Required, one of: GK (goalkeeper), DF (defender), MF (midfielder), FW (forward)
- **number**: Required, integer between 1 and 99
- **status**: Required, one of: active, injured, retired
- **club_id**: Required, must reference an existing club

### Constraints
- Jersey number must be unique within a club (two players in the same club cannot have the same number)

## Architecture

```
User Input → Intent Detection (regex from intents.json) → Handler (chatbot.py)
→ Service Layer (clubs_service.py / players_service.py) → Database (db.py)
```

Key principles:
- All DB access goes through `src/db.py` (no direct SQL in chatbot)
- Validation is enforced in service layer before database operations
- Custom exceptions: `PlayerValidationError`, `PlayerNotFoundError`, `ClubNotFoundError`
- Responses are user-friendly Bulgarian messages

## Testing

Run unit tests:
```bash
python -m pytest tests/test_players_service.py -v
```

Or using unittest:
```bash
python -m unittest tests.test_players_service -v
```

The test suite includes:
- Validation tests (position, number, birthdate, status)
- CRUD operation tests (create, read, update, delete)
- Filtering and pagination tests
- Error handling tests (missing data, invalid input, duplicate numbers)
- Full integration workflow test

## Test Data

Sample data is provided in `data/test_players.sql`. To load it:
```bash
python -c "from src.db import execute_query; execute_query(open('data/test_players.sql').read(), commit=True)"
```

Or manually via SQLite:
```bash
sqlite3 data.db < data/test_players.sql
```

## Players Service API

### Functions

#### `add_player(full_name, birth_date, nationality, position, number, club_name) → str`
Adds a new player. Returns success message. Raises `PlayerValidationError` or `ClubNotFoundError`.

#### `get_players(club_id=None, limit=None, offset=0) → List[Dict]`
Retrieves players with optional filtering by club_id and pagination.

#### `get_players_by_club_name(club_name) → List[Dict]`
Retrieves all players for a specific club. Raises `ClubNotFoundError` if club doesn't exist.

#### `update_player(player_id, position=None, number=None, status=None) → str`
Updates player's position, number, or status. Returns success message. Raises `PlayerNotFoundError` or `PlayerValidationError`.

#### `update_player_number(name, number) → str`
Legacy function: updates player's number by name.

#### `update_player_status(name, status) → str`
Updates player's status by name.

#### `delete_player(player_id) → str`
Deletes a player by ID (hard delete). Returns success message. Raises `PlayerNotFoundError`.

#### `delete_player_by_name(name) → str`
Legacy function: deletes a player by name.

#### `format_player_list(players) → str`
Formats a list of player dictionaries for display.

## Git commit suggestions (minimal required)
1. initial commit
2. add db module
3. add chatbot base + intents
4. add clubs CRUD
5. add players CRUD + validation
6. add tests and documentation
