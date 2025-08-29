import requests
import sqlite3
import json

DB_PATH = "mtg.db"

# Step 1: Get the latest bulk card data metadata
bulk_url = "https://api.scryfall.com/bulk-data"
bulk_meta = requests.get(bulk_url).json()

# Find the "default_cards" bulk file (contains all non-digital, real MTG cards)
default_cards_uri = next(
    d["download_uri"] for d in bulk_meta["data"] if d["type"] == "default_cards"
)

print("Downloading card data...")
cards_json = requests.get(default_cards_uri).json()
print(f"Downloaded {len(cards_json)} cards.")

# Step 2: Create SQLite database
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS cards")

cur.execute("""
CREATE TABLE cards_raw (
    id TEXT PRIMARY KEY,
    json TEXT
)
""")

# Step 3: Insert raw JSON data
for card in cards_json:
    cur.execute("""
    INSERT OR IGNORE INTO cards_raw (id, json)
    VALUES (?, ?)
    """, (
        card["id"],
        json.dumps(card)   # convert the whole card dict to a JSON string
    ))

conn.commit()
conn.close()

print(f"Database saved to {DB_PATH}")
