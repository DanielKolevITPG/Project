import sys
import os
sys.path.insert(0, ".")
from src.database.db import get_connection

# Delete the database file to start completely fresh
db_path = "C:\\Users\\Students\\Desktop\\test\\Project\\data.db"
if os.path.exists(db_path):
    os.remove(db_path)

# Get a fresh connection (will create new database)
conn = get_connection()

# Create tables
with open('sql/schema.sql', 'r') as f:
    conn.executescript(f.read())
conn.commit()

# Load seed data
with open('data/seed_data.sql', 'r', encoding='utf-8') as f:
    conn.executescript(f.read())
conn.commit()

print("Database initialized with seed data for all phases")