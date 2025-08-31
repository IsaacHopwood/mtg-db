import requests
import sqlite3
import time
import json
from bs4 import BeautifulSoup

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

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/127.0.0.0 Safari/537.36"
}

# Fetch the public precons page (HTML)
public_url = "https://moxfield.com/decks/public?q=eyJmb3JtYXQiOiJjb21tYW5kZXJQcmVjb25zIn0%3D"
resp = requests.get(public_url, headers=headers)
resp.raise_for_status()
html = resp.text

# Parse HTML to extract deck IDs
soup = BeautifulSoup(html, "html.parser")
deck_elements = soup.find_all("div", {"data-publicid": True})
deck_ids = [el["data-publicid"] for el in deck_elements]

# Loop over each deck_id to fetch full deck JSON and insert into database
for deck_id in deck_ids:
    deck_url = f"https://api2.moxfield.com/v3/decks/all/{deck_id}"
    deck_resp = requests.get(deck_url, headers=headers)
    deck_resp.raise_for_status()
    deck_json = deck_resp.text
    deck_data = deck_resp.json()

    name = deck_data.get("name")
    fmt = deck_data.get("format")
    created = deck_data.get("createdAtUtc")
    updated = deck_data.get("updatedAtUtc")
    owner = deck_data.get("createdByUser") or "WizardsOfTheCoast"

    cursor.execute("""
    INSERT OR REPLACE INTO precons (id, name, format, created, updated, owner, json)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (deck_id, name, fmt, created, updated, owner, deck_json))
    conn.commit()
    print(f"Saved deck {name} ({deck_id})")
    time.sleep(0.5)

print("All precons imported successfully!")

conn.close()