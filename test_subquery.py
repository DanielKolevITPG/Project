import sys
sys.path.insert(0, '.')
from src.database.db import get_connection
conn = get_connection()

# Test the subquery
result = conn.execute("SELECT id FROM leagues WHERE name = 'Първа Лига'").fetchone()
print('League ID:', result[0] if result else 'None')

result = conn.execute("SELECT id FROM clubs WHERE name = 'Левски София'").fetchone()
print('Club ID:', result[0] if result else 'None')