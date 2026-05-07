import sys
sys.path.insert(0, '.')
from src.database.db import get_connection
conn = get_connection()

print("Leagues:")
result = conn.execute("SELECT name, season FROM leagues").fetchall()
for r in result:
    print(f"  {r[0]} {r[1]}")

print("\nClubs:")
result = conn.execute("SELECT name FROM clubs").fetchall()
for r in result:
    print(f"  {r[0]}")

print("\nMatches:")
result = conn.execute("SELECT league_id, home_club_id, away_club_id, home_goals, away_goals, status FROM matches LIMIT 5").fetchall()
for r in result:
    print(f"  League ID: {r[0]}, Home: {r[1]}, Away: {r[2]}, Score: {r[3]}:{r[4]}, Status: {r[5]}")