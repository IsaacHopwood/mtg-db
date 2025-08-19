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
CREATE TABLE cards (
    id TEXT PRIMARY KEY,
    name TEXT,
    mana_cost TEXT,
    type_line TEXT,
    oracle_text TEXT,
    set_code TEXT,
    rarity TEXT,
    colors TEXT,
    image_uri TEXT
)
""")

# Step 3: Insert data
for card in cards_json:
    cur.execute("""
    INSERT OR IGNORE INTO cards
        (id, name, mana_cost, type_line, oracle_text, set_code, rarity, colors, image_uri)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        card["id"],
        card["name"],
        card.get("mana_cost"),
        card.get("type_line"),
        card.get("oracle_text"),
        card["set"],
        card["rarity"],
        json.dumps(card.get("colors")),
        card["image_uris"]["normal"] if "image_uris" in card else None
    ))

conn.commit()
conn.close()

print(f"Database saved to {DB_PATH}")
