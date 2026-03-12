import unittest
import os
import sys
import tempfile
import sqlite3
from datetime import datetime

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db import get_connection, execute_query
from src.players_service import (
    add_player,
    get_players,
    get_players_by_club_name,
    update_player,
    update_player_number,
    update_player_status,
    delete_player,
    delete_player_by_name,
    format_player_list,
    PlayerValidationError,
    PlayerNotFoundError,
    ClubNotFoundError,
    validate_position,
    validate_number,
    validate_birthdate,
    validate_status
)
from src.clubs_service import add_club


class TestPlayersService(unittest.TestCase):
    """Test suite for players_service module."""

    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        # Create a temporary database for testing
        cls.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        cls.test_db.close()
        os.environ['TEST_DB_PATH'] = cls.test_db.name

        # Initialize database with schema
        conn = sqlite3.connect(cls.test_db.name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Create tables
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS clubs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                birth_date TEXT NOT NULL,
                nationality TEXT NOT NULL,
                position TEXT NOT NULL CHECK(position IN ('GK', 'DF', 'MF', 'FW')),
                number INTEGER NOT NULL CHECK(number >= 1 AND number <= 99),
                status TEXT NOT NULL DEFAULT 'active',
                club_id INTEGER NOT NULL,
                FOREIGN KEY (club_id) REFERENCES clubs(id)
            );

            CREATE INDEX IF NOT EXISTS idx_players_club_id ON players(club_id);
        ''')
        conn.commit()

        # Insert test clubs
        cursor.execute("INSERT INTO clubs (name) VALUES ('Тестов Клуб 1')")
        cursor.execute("INSERT INTO clubs (name) VALUES ('Тестов Клуб 2')")
        conn.commit()

        # Get club IDs
        cls.club1_id = cursor.execute("SELECT id FROM clubs WHERE name = 'Тестов Клуб 1'").fetchone()['id']
        cls.club2_id = cursor.execute("SELECT id FROM clubs WHERE name = 'Тестов Клуб 2'").fetchone()['id']

        conn.close()

        # Override the global connection in db module
        import src.db as db_module
        db_module._conn = sqlite3.connect(cls.test_db.name)
        db_module._conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        import src.db as db_module
        if db_module._conn:
            db_module._conn.close()
            db_module._conn = None
        os.unlink(cls.test_db.name)

    def setUp(self):
        """Clear data before each test."""
        conn = sqlite3.connect(self.test_db.name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM players")
        cursor.execute("DELETE FROM clubs")
        # Reinsert clubs
        cursor.execute("INSERT INTO clubs (name) VALUES ('Тестов Клуб 1')")
        cursor.execute("INSERT INTO clubs (name) VALUES ('Тестов Клуб 2')")
        conn.commit()
        self.club1_id = cursor.execute("SELECT id FROM clubs WHERE name = 'Тестов Клуб 1'").fetchone()['id']
        self.club2_id = cursor.execute("SELECT id FROM clubs WHERE name = 'Тестов Клуб 2'").fetchone()['id']
        conn.close()

    # ========== VALIDATION TESTS ==========

    def test_validate_position_valid(self):
        """Test position validation with valid positions."""
        for pos in VALID_POSITIONS:
            self.assertTrue(validate_position(pos))

    def test_validate_position_invalid(self):
        """Test position validation with invalid positions."""
        self.assertFalse(validate_position('ST'))
        self.assertFalse(validate_position(''))
        self.assertFalse(validate_position(None))

    def test_validate_number_valid(self):
        """Test number validation with valid numbers."""
        for num in [1, 50, 99]:
            self.assertTrue(validate_number(num))

    def test_validate_number_invalid(self):
        """Test number validation with invalid numbers."""
        self.assertFalse(validate_number(0))
        self.assertFalse(validate_number(100))
        self.assertFalse(validate_number(-5))
        self.assertFalse(validate_number('10'))

    def test_validate_birthdate_valid(self):
        """Test birthdate validation with valid past dates."""
        self.assertTrue(validate_birthdate('1990-01-01'))
        self.assertTrue(validate_birthdate('2000-12-31'))

    def test_validate_birthdate_invalid(self):
        """Test birthdate validation with invalid dates."""
        self.assertFalse(validate_birthdate('2025-01-01'))  # Future date
        self.assertFalse(validate_birthdate('invalid-date'))
        self.assertFalse(validate_birthdate(''))
        self.assertFalse(validate_birthdate(None))

    def test_validate_status_valid(self):
        """Test status validation with valid statuses."""
        for status in VALID_STATUS:
            self.assertTrue(validate_status(status))

    def test_validate_status_invalid(self):
        """Test status validation with invalid statuses."""
        self.assertFalse(validate_status('available'))
        self.assertFalse(validate_status(''))
        self.assertFalse(validate_status(None))

    # ========== ADD PLAYER TESTS ==========

    def test_add_player_success(self):
        """Test successful player addition."""
        result = add_player(
            full_name='Иван Петров',
            birth_date='1995-05-15',
            nationality='България',
            position='FW',
            number=10,
            club_name='Тестов Клуб 1'
        )
        self.assertIn('успешно', result)

        # Verify player was added
        players = get_players_by_club_name('Тестов Клуб 1')
        self.assertEqual(len(players), 1)
        self.assertEqual(players[0]['full_name'], 'Иван Петров')

    def test_add_player_missing_required_fields(self):
        """Test add player with missing required fields."""
        with self.assertRaises(PlayerValidationError):
            add_player('', '1990-01-01', 'България', 'FW', 10, 'Тестов Клуб 1')

        with self.assertRaises(PlayerValidationError):
            add_player('Иван Петров', '', 'България', 'FW', 10, 'Тестов Клуб 1')

        with self.assertRaises(PlayerValidationError):
            add_player('Иван Петров', '1990-01-01', '', 'FW', 10, 'Тестов Клуб 1')

    def test_add_player_invalid_position(self):
        """Test add player with invalid position."""
        with self.assertRaises(PlayerValidationError):
            add_player(
                'Иван Петров',
                '1990-01-01',
                'България',
                'ST',
                10,
                'Тестов Клуб 1'
            )

    def test_add_player_invalid_number(self):
        """Test add player with invalid number."""
        with self.assertRaises(PlayerValidationError):
            add_player(
                'Иван Петров',
                '1990-01-01',
                'България',
                'FW',
                0,
                'Тестов Клуб 1'
            )

        with self.assertRaises(PlayerValidationError):
            add_player(
                'Иван Петров',
                '1990-01-01',
                'България',
                'FW',
                100,
                'Тестов Клуб 1'
            )

    def test_add_player_invalid_birthdate(self):
        """Test add player with invalid birthdate."""
        with self.assertRaises(PlayerValidationError):
            add_player(
                'Иван Петров',
                '2025-01-01',
                'България',
                'FW',
                10,
                'Тестов Клуб 1'
            )

    def test_add_player_club_not_found(self):
        """Test add player with non-existent club."""
        with self.assertRaises(ClubNotFoundError):
            add_player(
                'Иван Петров',
                '1990-01-01',
                'България',
                'FW',
                10,
                'Несъществуващ Клуб'
            )

    def test_add_player_duplicate_number(self):
        """Test add player with duplicate jersey number in same club."""
        add_player(
            'Иван Петров',
            '1990-01-01',
            'България',
            'FW',
            10,
            'Тестов Клуб 1'
        )

        with self.assertRaises(PlayerValidationError):
            add_player(
                'Петър Иванов',
                '1992-03-20',
                'България',
                'MF',
                10,
                'Тестов Клуб 1'
            )

    def test_add_player_same_number_different_club(self):
        """Test add player with same jersey number in different club (should succeed)."""
        add_player(
            'Иван Петров',
            '1990-01-01',
            'България',
            'FW',
            10,
            'Тестов Клуб 1'
        )

        # Should succeed - same number in different club
        result = add_player(
            'Петър Иванов',
            '1992-03-20',
            'България',
            'MF',
            10,
            'Тестов Клуб 2'
        )
        self.assertIn('успешно', result)

    # ========== GET PLAYERS TESTS ==========

    def test_get_players_empty(self):
        """Test get players with no players."""
        players = get_players()
        self.assertEqual(len(players), 0)

    def test_get_players_all(self):
        """Test get all players."""
        add_player('Игрок 1', '1990-01-01', 'България', 'FW', 10, 'Тестов Клуб 1')
        add_player('Игрок 2', '1991-01-01', 'България', 'MF', 8, 'Тестов Клуб 1')
        add_player('Игрок 3', '1992-01-01', 'България', 'DF', 4, 'Тестов Клуб 2')

        players = get_players()
        self.assertEqual(len(players), 3)

    def test_get_players_by_club_id(self):
        """Test get players filtered by club_id."""
        add_player('Игрок 1', '1990-01-01', 'България', 'FW', 10, 'Тестов Клуб 1')
        add_player('Игрок 2', '1991-01-01', 'България', 'MF', 8, 'Тестов Клуб 1')
        add_player('Игрок 3', '1992-01-01', 'България', 'DF', 4, 'Тестов Клуб 2')

        players_club1 = get_players(club_id=self.club1_id)
        self.assertEqual(len(players_club1), 2)

        players_club2 = get_players(club_id=self.club2_id)
        self.assertEqual(len(players_club2), 1)

    def test_get_players_pagination(self):
        """Test get players with pagination."""
        for i in range(10):
            add_player(
                f'Игрок {i+1}',
                f'199{i}-01-01',
                'България',
                'FW',
                i+1,
                'Тестов Клуб 1'
            )

        # Get first 5
        players = get_players(limit=5)
        self.assertEqual(len(players), 5)

        # Get next 5
        players = get_players(limit=5, offset=5)
        self.assertEqual(len(players), 5)

    def test_get_players_by_club_name(self):
        """Test get players by club name."""
        add_player('Игрок 1', '1990-01-01', 'България', 'FW', 10, 'Тестов Клуб 1')

        players = get_players_by_club_name('Тестов Клуб 1')
        self.assertEqual(len(players), 1)
        self.assertEqual(players[0]['full_name'], 'Игрок 1')

    def test_get_players_by_club_name_not_found(self):
        """Test get players with non-existent club name."""
        with self.assertRaises(ClubNotFoundError):
            get_players_by_club_name('Несъществуващ Клуб')

    # ========== UPDATE PLAYER TESTS ==========

    def test_update_player_number_success(self):
        """Test successful player number update."""
        add_player('Иван Петров', '1990-01-01', 'България', 'FW', 10, 'Тестов Клуб 1')

        result = update_player_number('Иван Петров', 11)
        self.assertIn('актуализиран', result)

        # Verify update
        players = get_players_by_club_name('Тестов Клуб 1')
        self.assertEqual(players[0]['number'], 11)

    def test_update_player_number_not_found(self):
        """Test update number for non-existent player."""
        with self.assertRaises(PlayerNotFoundError):
            update_player_number('Несъществуващ Игрок', 10)

    def test_update_player_number_invalid(self):
        """Test update player with invalid number."""
        add_player('Иван Петров', '1990-01-01', 'България', 'FW', 10, 'Тестов Клуб 1')

        with self.assertRaises(PlayerValidationError):
            update_player_number('Иван Петров', 0)

    def test_update_player_number_duplicate(self):
        """Test update player number to duplicate in same club."""
        add_player('Игрок 1', '1990-01-01', 'България', 'FW', 10, 'Тестов Клуб 1')
        add_player('Игрок 2', '1991-01-01', 'България', 'MF', 11, 'Тестов Клуб 1')

        with self.assertRaises(PlayerValidationError):
            update_player_number('Игрок 2', 10)

    def test_update_player_status_success(self):
        """Test successful player status update."""
        add_player('Иван Петров', '1990-01-01', 'България', 'FW', 10, 'Тестов Клуб 1')

        result = update_player_status('Иван Петров', 'injured')
        self.assertIn('актуализиран', result)

        # Verify update
        players = get_players_by_club_name('Тестов Клуб 1')
        self.assertEqual(players[0]['status'], 'injured')

    def test_update_player_status_invalid(self):
        """Test update player with invalid status."""
        add_player('Иван Петров', '1990-01-01', 'България', 'FW', 10, 'Тестов Клуб 1')

        with self.assertRaises(PlayerValidationError):
            update_player_status('Иван Петров', 'available')

    def test_update_player_position(self):
        """Test update player position."""
        add_player('Иван Петров', '1990-01-01', 'България', 'FW', 10, 'Тестов Клуб 1')

        result = update_player(player_id=1, position='MF')
        self.assertIn('актуализиран', result)

        players = get_players_by_club_name('Тестов Клуб 1')
        self.assertEqual(players[0]['position'], 'MF')

    def test_update_player_multiple_fields(self):
        """Test update multiple player fields at once."""
        add_player('Иван Петров', '1990-01-01', 'България', 'FW', 10, 'Тестов Клуб 1')

        result = update_player(
            player_id=1,
            position='MF',
            number=7,
            status='injured'
        )
        self.assertIn('актуализиран', result)

        players = get_players_by_club_name('Тестов Клуб 1')
        player = players[0]
        self.assertEqual(player['position'], 'MF')
        self.assertEqual(player['number'], 7)
        self.assertEqual(player['status'], 'injured')

    def test_update_player_no_changes(self):
        """Test update player with no changes."""
        add_player('Иван Петров', '1990-01-01', 'България', 'FW', 10, 'Тестов Клуб 1')

        result = update_player(player_id=1)
        self.assertEqual(result, 'Няма промени за прилагане.')

    def test_update_player_not_found(self):
        """Test update non-existent player."""
        with self.assertRaises(PlayerNotFoundError):
            update_player(player_id=999)

    # ========== DELETE PLAYER TESTS ==========

    def test_delete_player_success(self):
        """Test successful player deletion."""
        add_player('Иван Петров', '1990-01-01', 'България', 'FW', 10, 'Тестов Клуб 1')

        result = delete_player_by_name('Иван Петров')
        self.assertIn('изтрит', result)

        # Verify deletion
        players = get_players_by_club_name('Тестов Клуб 1')
        self.assertEqual(len(players), 0)

    def test_delete_player_by_id_success(self):
        """Test successful player deletion by ID."""
        add_player('Иван Петров', '1990-01-01', 'България', 'FW', 10, 'Тестов Клуб 1')

        # Get player ID
        players = get_players_by_club_name('Тестов Клуб 1')
        player_id = players[0]['id']

        result = delete_player(player_id)
        self.assertIn('изтрит', result)

        # Verify deletion
        players = get_players()
        self.assertEqual(len(players), 0)

    def test_delete_player_not_found(self):
        """Test delete non-existent player."""
        with self.assertRaises(PlayerNotFoundError):
            delete_player_by_name('Несъществуващ Игрок')

    def test_delete_player_by_id_not_found(self):
        """Test delete non-existent player by ID."""
        with self.assertRaises(PlayerNotFoundError):
            delete_player(999)

    # ========== FORMAT PLAYER LIST TESTS ==========

    def test_format_player_list_empty(self):
        """Test format empty player list."""
        result = format_player_list([])
        self.assertEqual(result, 'Няма намерени играчи.')

    def test_format_player_list_with_data(self):
        """Test format player list with data."""
        players = [
            {
                'full_name': 'Иван Петров',
                'position': 'FW',
                'number': 10,
                'nationality': 'България',
                'status': 'active'
            }
        ]
        result = format_player_list(players)
        self.assertIn('Иван Петров', result)
        self.assertIn('FW', result)
        self.assertIn('#10', result)

    # ========== INTEGRATION TESTS ==========

    def test_full_crud_workflow(self):
        """Test complete CRUD workflow."""
        # Create
        result = add_player(
            'Иван Петров',
            '1990-01-01',
            'България',
            'FW',
            10,
            'Тестов Клуб 1'
        )
        self.assertIn('успешно', result)

        # Read
        players = get_players_by_club_name('Тестов Клуб 1')
        self.assertEqual(len(players), 1)
        player_id = players[0]['id']

        # Update
        result = update_player(
            player_id=player_id,
            number=11,
            status='injured'
        )
        self.assertIn('актуализиран', result)

        players = get_players_by_club_name('Тестов Клуб 1')
        self.assertEqual(players[0]['number'], 11)
        self.assertEqual(players[0]['status'], 'injured')

        # Delete
        result = delete_player(player_id)
        self.assertIn('изтрит', result)

        players = get_players_by_club_name('Тестов Клуб 1')
        self.assertEqual(len(players), 0)


if __name__ == '__main__':
    unittest.main()
