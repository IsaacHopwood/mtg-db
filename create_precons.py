import requests
import sqlite3
import time

# SQLite database file
db_path = "mtg.db"

# Create a connection
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create new table for precons with owner column
cursor.execute("""
DROP TABLE IF EXISTS precons;
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS precons (
    id TEXT PRIMARY KEY,
    name TEXT,
    format TEXT,
    created DATE,
    updated DATE,
    owner TEXT,
    json TEXT
)
""")
conn.commit()

# Base API URL for fetching decks using search endpoint
search_url = "https://api2.moxfield.com/v2/decks/search"
page = 1

while True:
    print(f"Fetching page {page}...")

    resp = requests.get(
        search_url,
        params={
            "q": '{"format":"commanderPrecons"}',
            "pageNumber": page,
            "pageSize": 50
        },
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/127.0.0.0 Safari/537.36"
        }
    )
    resp.raise_for_status()
    data = resp.json()
    decks = data.get("data", [])
    if not decks:
        break

    for deck in decks:
        if "Commander Precons" not in deck.get("hubNames", []):
            continue  # skip non-official precons

        deck_id = deck["publicId"]
        name = deck["name"]
        fmt = deck.get("format")
        created = deck.get("createdAtUtc")
        updated = deck.get("updatedAtUtc")
        owner = deck.get("createdByUser") or "WizardsOfTheCoast"

        # Fetch full deck JSON
        deck_url = f"https://api2.moxfield.com/v3/decks/all/{deck_id}"
        deck_resp = requests.get(deck_url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/127.0.0.0 Safari/537.36"
        })
        deck_resp.raise_for_status()
        deck_json = deck_resp.text

        cursor.execute("""
        INSERT OR REPLACE INTO precons (id, name, format, created, updated, owner, json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (deck_id, name, fmt, created, updated, owner, deck_json))
        conn.commit()
        print(f"Saved deck {name} ({deck_id})")

        time.sleep(0.5)

    page += 1

print("All precons imported successfully!")

conn.close()