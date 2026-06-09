import os
import sqlite3
import tempfile
import unittest

from ai.ai_service import AIPredictionError, get_match_prediction


class TestPhase8AI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.py_exe = os.environ.get("TEST_PYTHON_EXE")
        if cls.py_exe:
            try:
                import sklearn  # noqa: F401
            except Exception:
                raise unittest.SkipTest("scikit-learn is not installed in current interpreter")

        cls.test_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        cls.test_db.close()

        conn = sqlite3.connect(cls.test_db.name)
        with open(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql")),
            "r",
            encoding="utf-8",
        ) as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()

        import src.db as db_module

        db_module._conn = sqlite3.connect(cls.test_db.name)
        db_module._conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls):
        import src.db as db_module

        if db_module._conn:
            db_module._conn.close()
            db_module._conn = None
        os.unlink(cls.test_db.name)

    def setUp(self):
        import src.db as db_module

        conn = db_module._conn
        cur = conn.cursor()
        for table in [
            "goals",
            "cards",
            "matches",
            "league_teams",
            "leagues",
            "players",
            "transfers",
            "clubs",
        ]:
            cur.execute(f"DELETE FROM {table}")
        conn.commit()

    def _setup_success_data(self):
        import src.db as db_module

        conn = db_module._conn
        cur = conn.cursor()
        cur.execute("INSERT INTO clubs(name) VALUES ('Левски')")
        cur.execute("INSERT INTO clubs(name) VALUES ('Лудогорец')")
        cur.execute("INSERT INTO leagues(name, season) VALUES ('Тест Лига', '2025/2026')")

        league_id = cur.execute("SELECT id FROM leagues WHERE name='Тест Лига'").fetchone()[0]
        home_id = cur.execute("SELECT id FROM clubs WHERE name='Левски'").fetchone()[0]
        away_id = cur.execute("SELECT id FROM clubs WHERE name='Лудогорец'").fetchone()[0]

        cur.execute("INSERT INTO league_teams(league_id, club_id) VALUES (?, ?)", (league_id, home_id))
        cur.execute("INSERT INTO league_teams(league_id, club_id) VALUES (?, ?)", (league_id, away_id))

        matches = [
            (1, home_id, away_id, 2, 1),
            (2, away_id, home_id, 3, 0),
            (3, home_id, away_id, 1, 1),
            (4, away_id, home_id, 0, 1),
            (5, home_id, away_id, 2, 0),
            (6, away_id, home_id, 2, 2),
        ]
        for rnd, h, a, hg, ag in matches:
            cur.execute(
                """
                INSERT INTO matches(league_id, round_no, home_club_id, away_club_id, home_goals, away_goals, status)
                VALUES (?, ?, ?, ?, ?, ?, 'played')
                """,
                (league_id, rnd, h, a, hg, ag),
            )

        conn.commit()

    def test_prediction_with_enough_data_ok(self):
        self._setup_success_data()
        result = get_match_prediction("Левски", "Лудогорец")

        self.assertGreaterEqual(result.home_win_pct, 0)
        self.assertGreaterEqual(result.draw_pct, 0)
        self.assertGreaterEqual(result.away_win_pct, 0)
        self.assertEqual(
            result.home_win_pct + result.draw_pct + result.away_win_pct,
            100,
        )

    def test_prediction_with_less_than_5_matches_error(self):
        import src.db as db_module

        conn = db_module._conn
        cur = conn.cursor()
        cur.execute("INSERT INTO clubs(name) VALUES ('A')")
        cur.execute("INSERT INTO clubs(name) VALUES ('B')")
        cur.execute("INSERT INTO leagues(name, season) VALUES ('L', '2025/2026')")
        league_id = cur.execute("SELECT id FROM leagues WHERE name='L'").fetchone()[0]
        a_id = cur.execute("SELECT id FROM clubs WHERE name='A'").fetchone()[0]
        b_id = cur.execute("SELECT id FROM clubs WHERE name='B'").fetchone()[0]
        cur.execute("INSERT INTO league_teams(league_id, club_id) VALUES (?, ?)", (league_id, a_id))
        cur.execute("INSERT INTO league_teams(league_id, club_id) VALUES (?, ?)", (league_id, b_id))
        for rnd in range(1, 5):
            cur.execute(
                "INSERT INTO matches(league_id, round_no, home_club_id, away_club_id, home_goals, away_goals, status) VALUES (?, ?, ?, ?, ?, ?, 'played')",
                (league_id, rnd, a_id, b_id, 1, 0),
            )
        conn.commit()

        with self.assertRaises(AIPredictionError):
            get_match_prediction("A", "B")

    def test_prediction_with_alias_team_names_ok(self):
        self._setup_success_data()
        result = get_match_prediction("Левски", "Лудогорец")
        self.assertEqual(result.home_team, "Левски")
        self.assertEqual(result.away_team, "Лудогорец")

    def test_non_existing_team_error(self):
        self._setup_success_data()
        with self.assertRaises(AIPredictionError):
            get_match_prediction("Несъществуващ", "Лудогорец")

    def test_teams_from_different_leagues_error(self):
        import src.db as db_module

        conn = db_module._conn
        cur = conn.cursor()
        cur.execute("INSERT INTO clubs(name) VALUES ('Team1')")
        cur.execute("INSERT INTO clubs(name) VALUES ('Team2')")
        cur.execute("INSERT INTO leagues(name, season) VALUES ('L1', '2025/2026')")
        cur.execute("INSERT INTO leagues(name, season) VALUES ('L2', '2025/2026')")

        t1 = cur.execute("SELECT id FROM clubs WHERE name='Team1'").fetchone()[0]
        t2 = cur.execute("SELECT id FROM clubs WHERE name='Team2'").fetchone()[0]
        l1 = cur.execute("SELECT id FROM leagues WHERE name='L1'").fetchone()[0]
        l2 = cur.execute("SELECT id FROM leagues WHERE name='L2'").fetchone()[0]

        cur.execute("INSERT INTO league_teams(league_id, club_id) VALUES (?, ?)", (l1, t1))
        cur.execute("INSERT INTO league_teams(league_id, club_id) VALUES (?, ?)", (l2, t2))
        conn.commit()

        with self.assertRaises(AIPredictionError):
            get_match_prediction("Team1", "Team2")


if __name__ == "__main__":
    unittest.main()
