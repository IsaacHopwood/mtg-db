import sqlite3
import json

conn = sqlite3.connect("mtg.db")
cur = conn.cursor()

# List all tables in the database
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()
print("Tables in database:", tables)

# Example: find blue instants that draw a card
cur.execute("""
SELECT json
FROM cards_raw
LIMIT 1000;
""")

for row in cur.fetchall():
    card_data = json.loads(row[0])  # parse JSON
    # filter manually
    if (
        'Instant' in card_data.get('type_line', '') and
        'draw a card' in card_data.get('oracle_text', '').lower() and
        'U' in card_data.get('colors', [])
    ):
        print(
            card_data.get('name'),
            card_data.get('mana_cost'),
            card_data.get('type_line')
        )

conn.close()