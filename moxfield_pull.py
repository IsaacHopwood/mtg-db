import sqlite3
import requests
import json

DB_PATH = "mtg.db"  # adjust path if needed

def fetch_moxfield_deck(deck_id: str):
    url = f"https://api2.moxfield.com/v2/decks/all/{deck_id}/export"
    headers = {
        "User-Agent": "Mozilla/5.0",  # mimic a browser
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()  # raw deck JSON
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None


def save_deck_to_db(deck_id: str, deck_data: dict):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create table if it doesn’t exist
    cur.execute("""
    CREATE TABLE IF NOT EXISTS moxfield_decks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deck_id TEXT,
        card_name TEXT,
        quantity INTEGER,
        category TEXT
    )
    """)

    # The export JSON has categories like "mainboard", "sideboard"
    for section, cards in deck_data.get("boards", {}).items():
        for card in cards.get("cards", []):
            cur.execute("""
                INSERT INTO moxfield_decks (deck_id, card_name, quantity, category)
                VALUES (?, ?, ?, ?)
            """, (
                deck_id,
                card["card"]["name"],
                card["quantity"],
                section
            ))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    deck_id = "2xb7x1fUa067oaAJxajLmg"
    deck_data = fetch_moxfield_deck(deck_id)

    if deck_data:
        save_deck_to_db(deck_id, deck_data)
        print(f"Deck {deck_id} saved to database {DB_PATH}")