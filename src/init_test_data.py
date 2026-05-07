import sys
sys.path.insert(0, ".")
from src.database.db import get_connection

# Create tables
conn = get_connection()
with open('sql/schema.sql', 'r') as f:
    conn.executescript(f.read())
conn.commit()

# Add test data
conn.execute("INSERT OR IGNORE INTO clubs (name) VALUES ('Левски'), ('Лудогорец'), ('ЦСКА'), ('Ботев')")
conn.commit()

# Create league
conn.execute("INSERT OR IGNORE INTO leagues (name, season) VALUES ('Първа лига', '2025/2026')")
conn.commit()

# Get league and club IDs
league = conn.execute("SELECT id FROM leagues WHERE name='Първа лига' AND season='2025/2026'").fetchone()
levski = conn.execute("SELECT id FROM clubs WHERE name='Левски'").fetchone()
ludo = conn.execute("SELECT id FROM clubs WHERE name='Лудогорец'").fetchone()
cska = conn.execute("SELECT id FROM clubs WHERE name='ЦСКА'").fetchone()
botev = conn.execute("SELECT id FROM clubs WHERE name='Ботев'").fetchone()

# Add teams to league
conn.execute(f"INSERT OR IGNORE INTO league_teams (league_id, club_id) VALUES ({league['id']}, {levski['id']})")
conn.execute(f"INSERT OR IGNORE INTO league_teams (league_id, club_id) VALUES ({league['id']}, {ludo['id']})")
conn.execute(f"INSERT OR IGNORE INTO league_teams (league_id, club_id) VALUES ({league['id']}, {cska['id']})")
conn.execute(f"INSERT OR IGNORE INTO league_teams (league_id, club_id) VALUES ({league['id']}, {botev['id']})")
conn.commit()

# Add some matches
conn.execute(f"INSERT INTO matches (league_id, round_no, home_club_id, away_club_id, home_goals, away_goals, status) VALUES ({league['id']}, 1, {levski['id']}, {ludo['id']}, 3, 1, 'played')")
conn.execute(f"INSERT INTO matches (league_id, round_no, home_club_id, away_club_id, home_goals, away_goals, status) VALUES ({league['id']}, 1, {cska['id']}, {botev['id']}, 2, 2, 'played')")
conn.commit()

print("Database initialized with test data")