# Football Manager — Stage 4 (Transfers)

Simple command-line chatbot to manage football clubs, players and transfers (SQLite backend).

## Structure
- src/
  - main.py           — entrypoint, main loop and logging
  - intents.json      — regex intent patterns and responses
  - chatbot/
    - nlu.py          — intent detection (regex)
    - router.py       — intent routing and handlers
  - services/
    - clubs_service.py    — Clubs CRUD operations
    - players_service.py — Players CRUD operations
    - transfers_service.py — Transfers with business logic
  - database/
    - db.py           — centralized DB connection + query helper
  - utils/
    - logger.py       — logging utilities
- sql/
  - schema.sql        — DB schema (clubs, players, transfers tables)
- data/
  - test_transfers.sql — Sample test data
- commands.log       — runtime log (created at first run)
- data.db            — SQLite database (created at first run)
- dialogue_example.md — Example conversations

## Installation
1. Ensure Python 3.8+
2. Clone repository
3. (Optional) create virtualenv and activate
4. No external packages required

## How to run
From project root:
- Windows (PowerShell or cmd):
  ```bash
  python src/main.py
  ```

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

### Transfers
- `Трансфер <име> от <клуб> в <клуб> <YYYY-MM-DD>` — Transfer a player
- `Трансфер <име> от <клуб> в <клуб> <YYYY-MM-DD> сума <сума>` — Transfer with fee
- `Покажи трансфери на <име>` — Show transfer history for a player
- `Покажи трансфери на клуб <клуб>` — Show all transfers for a club

### System
- `помощ` or `help` — Show help (all commands)
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
- `club_id` INTEGER (FK to clubs.id, can be NULL)
- Index on `club_id`

### transfers
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `player_id` INTEGER NOT NULL (FK to players.id)
- `from_club_id` INTEGER (FK to clubs.id, can be NULL for first club)
- `to_club_id` INTEGER NOT NULL (FK to clubs.id)
- `transfer_date` TEXT NOT NULL (YYYY-MM-DD)
- `fee` INTEGER (optional)
- `note` TEXT (optional)
- CHECK (to_club_id != from_club_id)
- Indexes on player_id, from_club_id, to_club_id, transfer_date

## Business Rules (Transfers)

1. Player must belong to the "from" club for transfer to succeed
2. Player with no club (NULL) can only be transferred from "none/free"
3. From and To clubs must be different
4. Transfer date must be valid YYYY-MM-DD format
5. Fee (if provided) must be non-negative
6. Transfer is atomic: both transfer record AND player update succeed or fail together

## Architecture

```
User Input → NLU (intents.json regex) → Router (chatbot/router.py)
    → Services (clubs/players/transfers_service.py) → Database (database/db.py)
```

Key principles:
- All DB access goes through `database/db.py` (no direct SQL in chatbot)
- Validation is enforced in service layer
- Custom exceptions: `PlayerValidationError`, `PlayerNotFoundError`, `ClubNotFoundError`, `TransferValidationError`
- Responses are user-friendly Bulgarian messages

## Test Data

Sample data is provided in `data/test_transfers.sql`. Includes:
- 4 clubs: Левски, Лудогорец, ЦСКА, Ботев Пловдив
- 6 players
- 5+ transfers

To load:
```bash
python -c "from src.database.db import execute_query; execute_query(open('data/test_transfers.sql').read(), commit=True)"
```

## Git Commits
- feat: transfers table + schema update
- feat: transfers service + business rules
- feat: chatbot intents update + main.py refactor
- test: seed data + scenarios
