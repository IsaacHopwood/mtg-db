import sqlite3

conn = sqlite3.connect("mtg.db")
cur = conn.cursor()

# Example: find blue instants that draw a card
cur.execute("""
SELECT name, mana_cost, type_line
FROM cards
WHERE type_line LIKE '%Instant%'
  AND oracle_text LIKE '%draw a card%'
  AND colors LIKE '%U%'
LIMIT 20;
""")

for row in cur.fetchall():
    print(row)

conn.close()
