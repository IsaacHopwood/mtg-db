import requests
import json
import sqlite3

DB_PATH = "mtg.db"  # adjust path if needed

def fetch_moxfield_deck(deck_id: str):
    url = f"https://api2.moxfield.com/v2/decks/all/{deck_id}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None


if __name__ == "__main__":
    deck_id = "2xb7x1fUa067oaAJxajLmg"
    deck_data = fetch_moxfield_deck(deck_id)

    if deck_data:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS moxfield_raw (
                deck_id TEXT PRIMARY KEY,
                data JSON
            )
        """)
        c.execute("""
            INSERT OR REPLACE INTO moxfield_raw (deck_id, data) VALUES (?, ?)
        """, (deck_id, json.dumps(deck_data)))
        conn.commit()
        conn.close()
        print(f"Deck {deck_id} saved to database.")